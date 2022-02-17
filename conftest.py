"""PyTest Fixtures."""
import os

os.environ["NO_COLOR"] = "1"
pytest_plugins = ["ansiblelint.testing.fixtures"]
