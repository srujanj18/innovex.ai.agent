import os

from app.tools.path_utils import resolve_workspace_path


def write_file(path: str, content: str, workspace_root: str | None = None) -> str:
    try:
        full_path = resolve_workspace_path(path, workspace_root)
        dir_name = os.path.dirname(full_path)

        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(content)

        return f"File written: {full_path}"
    except Exception as error:
        return f"Error writing file: {error}"
