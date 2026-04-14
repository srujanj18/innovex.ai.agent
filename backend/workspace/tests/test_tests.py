import unittest
from unittest.mock import MagicMock
import sys
import io
import os
import importlib.util
import subprocess

class TestTestsModule(unittest.TestCase):
    def test_main_runs_without_errors(self):
        process = subprocess.Popen(['python', 'tests.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        self.assertEqual(process.returncode, 0)

    def test_main_outputs_correct_message(self):
        process = subprocess.Popen(['python', 'tests.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        output = output.decode('utf-8')
        self.assertIn('Ran 1 test in', output)

    def test_main_discover_tests(self):
        spec = importlib.util.spec_from_file_location("tests", "tests.py")
        tests = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tests)
        loader = unittest.TestLoader()
        suite = loader.discover('tests', pattern='test_*.py')
        self.assertEqual(len(suite._tests), 1)

if __name__ == '__main__':
    unittest.main()