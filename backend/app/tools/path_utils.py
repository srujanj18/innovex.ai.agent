import os
from pathlib import Path


DEFAULT_WORKSPACE_ROOT = str(Path(__file__).resolve().parents[3])


def get_workspace_root(workspace_root: str | None = None) -> str:
    return os.path.abspath(workspace_root or DEFAULT_WORKSPACE_ROOT)


def _restore_missing_windows_drive(path: str, root: str) -> str:
    drive, _ = os.path.splitdrive(root)
    if not drive or not path:
        return path

    normalized = path.replace("/", "\\").lstrip("\\")
    if os.path.isabs(path) or os.path.splitdrive(normalized)[0]:
        return path

    if normalized.startswith("Users\\") or normalized.startswith("Program Files\\"):
        return f"{drive}\\{normalized}"

    return path


def _normalize_candidate_path(path: str, root: str) -> str:
    restored = _restore_missing_windows_drive(path, root)

    if os.path.isabs(restored):
        return os.path.abspath(restored)

    return os.path.abspath(os.path.join(root, restored))


def resolve_workspace_path(path: str, workspace_root: str | None = None) -> str:
    root = get_workspace_root(workspace_root)
    candidate = _normalize_candidate_path(path, root)

    if os.path.commonpath([root, candidate]) != root:
        raise ValueError(f"Path escapes workspace: {path}")

    return candidate


def to_workspace_relative_path(path: str, workspace_root: str | None = None) -> str:
    root = get_workspace_root(workspace_root)
    full_path = resolve_workspace_path(path, root)
    return os.path.relpath(full_path, root)
