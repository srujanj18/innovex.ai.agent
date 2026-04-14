from app.tools.path_utils import resolve_workspace_path


def edit_file(path: str, new_content: str, workspace_root: str | None = None) -> str:
    try:
        full_path = resolve_workspace_path(path, workspace_root)

        with open(full_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(new_content)

        return f"File updated: {full_path}"
    except Exception as error:
        return f"Error editing file: {error}"
