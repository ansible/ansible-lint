"""PyTest Fixtures."""
import importlib
import os
import sys
from typing import Any

from ansiblelint.schemas import refresh_schemas

# checking if user is running pytest without installing test dependencies:
missing = []
for module in ["ansible", "black", "flake8", "flaky", "mypy", "pylint", "pytest_cov"]:
    if not importlib.util.find_spec(module):
        missing.append(module)
if missing:
    print(
        f"FATAL: Missing modules: {', '.join(missing)} -- probably you missed installing test requirements with: pip install -e '.[test]'",
        file=sys.stderr,
    )
    sys.exit(1)


os.environ["NO_COLOR"] = "1"
pytest_plugins = ["ansiblelint.testing.fixtures"]


def pytest_configure(config: Any) -> None:
    """Configure pytest."""
    # run only on master node (xdist):
    if not hasattr(config, "slaveinput"):
        refresh_schemas()
