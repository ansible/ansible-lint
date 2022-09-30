"""PyTest Fixtures."""
import importlib
import os
import subprocess
import sys
from typing import Any

import pytest
from ansible.module_utils.common.yaml import HAS_LIBYAML

# checking if user is running pytest without installing test dependencies:
missing = []
for module in ["ansible", "black", "flake8", "flaky", "mypy", "pylint"]:
    if not importlib.util.find_spec(module):
        missing.append(module)
if missing:
    print(
        f"FATAL: Missing modules: {', '.join(missing)} -- probably you missed installing test requirements with: pip install -e '.[test]'",
        file=sys.stderr,
    )
    sys.exit(1)
# we need to be sure that we have the requirements installed as some tests
# might depend on these.
try:
    subprocess.check_output(
        ["ansible-galaxy", "collection", "install", "-r", "requirements.yml"],
        stderr=subprocess.PIPE,
        text=True,
    )
except subprocess.CalledProcessError as exc:
    print(f"{exc}\n{exc.stderr}\n{exc.stdout}", file=sys.stderr)
    sys.exit(1)

if not HAS_LIBYAML and sys.version_info >= (3, 9, 0):
    # While presence of libyaml is not required for runtime, we keep this error
    # fatal here in order to be sure that we spot libyaml errors during testing.
    #
    # For 3.8.x we do not do this check, as libyaml does not have an arm64 build for py38.
    print(
        "FATAL: For testing, we require pyyaml to be installed with its native extension, missing it would make testing 3x slower and risk missing essential bugs.",
        file=sys.stderr,
    )
    sys.exit(1)


os.environ["NO_COLOR"] = "1"


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
