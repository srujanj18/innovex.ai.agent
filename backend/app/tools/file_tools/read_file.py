import os

from app.tools.path_utils import resolve_workspace_path


def read_file(path: str, workspace_root: str | None = None) -> str:
    try:
        full_path = resolve_workspace_path(path, workspace_root)

        if not os.path.exists(full_path):
            return f"Error: File not found: {path}"

        with open(full_path, "r", encoding="utf-8") as file_handle:
            return file_handle.read()
    except Exception as error:
        return f"Error reading file: {error}"
