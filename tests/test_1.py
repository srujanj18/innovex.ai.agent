import unittest
import sys
import subprocess
import importlib.util
import os

# Try to import the module
module_path = os.path.abspath(os.path.join('..', '..', 'backend', 'workspace', '1.py'))
spec = importlib.util.spec_from_file_location("1", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Test1(unittest.TestCase):

    def test_hello_world(self):
        capturedOutput = sys.stdout
        sys.stdout = self._StringIO()
        module.main()
        sys.stdout = capturedOutput
        self.assertMultiLineEqual("Hello, world!\n", sys.stdout.getvalue())

    def test_hello_world_subprocess(self):
        with subprocess.Popen([sys.executable, module_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
            output = p.stdout.readlines()
            self.assertMultiLineEqual(b"Hello, world!\n", output)

class _StringIO:
    def __init__(self):
        self.string = []

    def write(self, value):
        self.string.append(value)

    def getvalue(self):
        return ''.join(self.string).encode()

if __name__ == '__main__':
    unittest.main()