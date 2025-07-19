import os
import unittest
from unittest.mock import patch

from nbh import cli


class TestCli(unittest.TestCase):
    def test_simple_notebook(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        notebook_path = os.path.join(fixtures_dir, "simple.ipynb")

        with patch("sys.argv", ["nbh", notebook_path]):
            # This will run the app function in cli.py with the mocked arguments
            # You can add assertions here to check the output or side effects
            cli.app()


if __name__ == "__main__":
    unittest.main()
