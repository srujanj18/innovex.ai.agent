import unittest
import subprocess
import sys

class Test1Module(unittest.TestCase):

    def test_print_and_exit(self):
        process = subprocess.Popen([sys.executable, '1.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        self.assertEqual(process.returncode, 0)
        self.assertEqual(output.decode('utf-8').strip(), "app is loaded")

if __name__ == '__main__':
    unittest.main()