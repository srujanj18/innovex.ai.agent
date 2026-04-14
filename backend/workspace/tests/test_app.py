import pathlib
import importlib.util
import subprocess
import sys
import unittest


WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET_FILE = WORKSPACE_ROOT / "app.py"
MODULE_NAME = "app"


def load_target_module():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, TARGET_FILE)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GeneratedSmokeTest(unittest.TestCase):
    def test_target_file_exists(self):
        self.assertTrue(TARGET_FILE.exists(), f"Missing target file: {TARGET_FILE}")

    def test_python_compiles(self):
        source = TARGET_FILE.read_text(encoding="utf-8")
        compile(source, "app.py", "exec")

    def test_module_imports(self):
        module = load_target_module()
        self.assertTrue(hasattr(module, "add_numbers"), "Expected function add_numbers to exist")
        self.assertTrue(hasattr(module, "chat"), "Expected function chat to exist")
        self.assertTrue(hasattr(module, "main"), "Expected function main to exist")

    def test_cli_invocation_finishes(self):
        result = subprocess.run(
            [sys.executable, str(TARGET_FILE)],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

if __name__ == "__main__":
    unittest.main()
