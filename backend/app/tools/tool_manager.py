from app.tools.file_tools.edit_file import edit_file
from app.tools.file_tools.read_file import read_file
from app.tools.file_tools.write_file import write_file
from app.tools.path_utils import get_workspace_root, to_workspace_relative_path
from app.tools.terminal.executor import run_command


class ToolManager:
    def __init__(self, workspace_root: str | None = None):
        self.workspace_root = get_workspace_root(workspace_root)
        self.changed_files: set[str] = set()
        self.tool_map = {
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "run_command": run_command,
        }

    def execute(self, tool_name: str, params: dict):
        print(f"\nTOOL CALL -> {tool_name}")
        print(f"PARAMS -> {params}")

        if tool_name not in self.tool_map:
            return f"Error: Unknown tool: {tool_name}"

        if not isinstance(params, dict):
            return "Error: Invalid parameters format (must be dict)"

        tool = self.tool_map[tool_name]

        try:
            if tool_name == "run_command":
                print("Executing terminal command...")

            tool_params = dict(params)

            if tool_name in {"read_file", "write_file", "edit_file", "run_command"}:
                tool_params["workspace_root"] = self.workspace_root

            result = tool(**tool_params)

            if tool_name in {"write_file", "edit_file"} and params.get("path"):
                self.changed_files.add(to_workspace_relative_path(params["path"], self.workspace_root))

            if result is None or result == "":
                return "OK: Tool executed successfully"

            return str(result)
        except TypeError as error:
            return f"Error: Parameter mismatch: {error}"
        except Exception as error:
            return f"Error: Tool execution failed: {error}"
