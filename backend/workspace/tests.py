import unittest
from unittest.mock import MagicMock
import sys

class TestOnePy(unittest.TestCase):
    def test_example(self):
        self.assertTrue(True)

def main():
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py', top_level_dir='.')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    main()