import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.agent_service import AgentService
from app.tools.path_utils import get_workspace_root, resolve_workspace_path

router = APIRouter()
BACKEND_WORKSPACE = str(Path(__file__).resolve().parents[3])


class ChatRequest(BaseModel):
    message: str
    task: Optional[str] = None
    filePath: Optional[str] = None
    relativeFilePath: Optional[str] = None
    language: Optional[str] = None
    code: Optional[str] = None
    selection: Optional[str] = None
    workspaceRoot: Optional[str] = None
    openFiles: Optional[List[str]] = None
    workspaceFiles: Optional[List[str]] = None
    runValidation: bool = False
    generateTests: bool = False
    autonomousMode: bool = True
    intelligenceLevel: str = "high"


class UpdatedFile(BaseModel):
    path: str
    content: str


def normalize_relative_path(file_path: str, workspace_root: Optional[str]) -> str:
    normalized_path = os.path.normpath(file_path)

    if workspace_root:
        normalized_root = os.path.normpath(workspace_root)
        try:
            relative_path = os.path.relpath(normalized_path, normalized_root)
            if not relative_path.startswith(".."):
                return relative_path
        except ValueError:
            pass

    return os.path.basename(normalized_path)


def get_agent_workspace_root(req: ChatRequest) -> str:
    return get_workspace_root(req.workspaceRoot or BACKEND_WORKSPACE)


def stage_editor_file(req: ChatRequest, workspace_root: str) -> Optional[str]:
    if not req.code:
        return None

    relative_path = req.relativeFilePath or (
        normalize_relative_path(req.filePath, req.workspaceRoot) if req.filePath else None
    )
    if not relative_path:
        return None

    destination = resolve_workspace_path(relative_path, workspace_root)
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    with open(destination, "w", encoding="utf-8") as file_handle:
        file_handle.write(req.code)

    return relative_path


def build_agent_prompt(req: ChatRequest, staged_path: Optional[str]) -> str:
    effective_path = staged_path or req.relativeFilePath or req.filePath
    parts = [req.message.strip()]

    context_fields = {
        "Task": req.task,
        "File path": effective_path,
        "Language": req.language,
        "Workspace root": req.workspaceRoot,
    }

    for label, value in context_fields.items():
        if value:
            parts.append(f"{label}: {value}")

    if req.openFiles:
        parts.append(f"Open files: {', '.join(req.openFiles)}")

    if req.workspaceFiles:
        parts.append("Workspace files:")
        parts.append("\n".join(req.workspaceFiles))

    if req.runValidation:
        parts.append("Run validation: true")

    if req.generateTests:
        parts.append("Generate tests: true")
    if req.autonomousMode:
        parts.append("Autonomous mode: true")
    if req.intelligenceLevel:
        parts.append(f"Intelligence level: {req.intelligenceLevel}")

    if req.selection:
        parts.append("Selected code:")
        parts.append(req.selection)

    if req.code:
        parts.append("Current file contents:")
        parts.append(req.code)

    return "\n\n".join(parts)


def collect_updated_files(agent: AgentService, workspace_root: str) -> List[UpdatedFile]:
    updated_files: List[UpdatedFile] = []

    for relative_path in agent.get_changed_files():
        content = agent.read_changed_file(relative_path)
        if content is None:
            continue

        updated_files.append(
            UpdatedFile(
                path=resolve_workspace_path(relative_path, workspace_root),
                content=content,
            )
        )

    return updated_files


@router.post("/chat")
def chat(req: ChatRequest):
    workspace_root = get_agent_workspace_root(req)
    agent = AgentService(workspace_root)
    staged_path = stage_editor_file(req, workspace_root)
    prompt = build_agent_prompt(req, staged_path)
    response = agent.process(
        prompt,
        autonomous_mode=req.autonomousMode,
        intelligence_level=req.intelligenceLevel,
    )
    updated_files = collect_updated_files(agent, workspace_root)

    return {
        "response": response,
        "task": req.task or "chat",
        "filePath": req.filePath,
        "runValidation": req.runValidation,
        "generateTests": req.generateTests,
        "autonomousMode": req.autonomousMode,
        "intelligenceLevel": req.intelligenceLevel,
        "updatedFiles": [item.model_dump() for item in updated_files],
    }
