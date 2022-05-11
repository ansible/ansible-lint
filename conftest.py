"""PyTest Fixtures."""
import importlib
import os
import sys
from typing import Any

import pytest

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


# pylint: disable=unused-argument
def pytest_addoption(
    parser: pytest.Parser, pluginmanager: pytest.PytestPluginManager
) -> None:
    """Add options to pytest."""
    parser.addoption(
        "--update-schemas",
        action="store_true",
        default=False,
        dest="update_schemas",
        help="update cached JSON schemas.",
    )


def pytest_configure(config: Any) -> None:
    """Configure pytest."""
    option = config.option
    # run only on master node (xdist):
    if option.update_schemas and not hasattr(config, "slaveinput"):
        # pylint: disable=import-outside-toplevel
        from ansiblelint.schemas import refresh_schemas

        if refresh_schemas():
            pytest.exit(
                "Schemas are outdated, please update them in a separate pull request.",
                1,
            )
        else:
            pytest.exit("Schemas already updated", 0)
