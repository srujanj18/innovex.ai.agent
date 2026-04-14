import subprocess

from app.tools.path_utils import get_workspace_root
from app.tools.terminal.validator import is_safe_command


def run_command(command: str, workspace_root: str | None = None):
    try:
        print(f"Running command: {command}")

        if isinstance(command, list):
            command = " ".join(command)

        if not is_safe_command(command):
            return f"Error: Unsafe command blocked: {command}"

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=20,
            cwd=get_workspace_root(workspace_root),
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        combined_output = "\n".join(part for part in [stdout, stderr] if part).strip()

        if result.returncode != 0:
            return f"Error: {combined_output or f'Command failed with exit code {result.returncode}'}"

        return combined_output if combined_output else "OK: Command executed"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as error:
        return f"Error: {error}"
