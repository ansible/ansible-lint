"""PyTest Fixtures."""

import importlib
import os
import platform
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

# Ensure we always run from the root of the repository
if Path.cwd() != Path(__file__).parent:
    os.chdir(Path(__file__).parent)

# checking if user is running pytest without installing test dependencies:
missing = [
    module
    for module in ["ansible", "black", "mypy", "pylint"]
    if not importlib.util.find_spec(module)
]
if missing:
    pytest.exit(
        reason=f"FATAL: Missing modules: {', '.join(missing)} -- probably you missed installing test requirements with: pip install -e '.[test]'",
        returncode=1,
    )


# See: https://github.com/pytest-dev/pytest/issues/1402#issuecomment-186299177
def pytest_configure(config: pytest.Config) -> None:
    """Ensure we run preparation only on master thread when running in parallel."""
    if is_help_option_present(config):
        return
    if is_master(config):
        # we need to be sure that we have the requirements installed as some tests
        # might depend on these. This approach is compatible with GHA caching.
        try:
            subprocess.check_output(
                ["./tools/install-reqs.sh"],  # noqa: S603
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            print(f"{exc}\n{exc.stderr}\n{exc.stdout}", file=sys.stderr)  # noqa: T201
            sys.exit(1)


def is_help_option_present(config: pytest.Config) -> bool:
    """Return true if pytest invocation was not about running tests."""
    return any(config.getoption(x) for x in ["--fixtures", "--help", "--collect-only"])


def is_master(config: pytest.Config) -> bool:
    """Return true if is run on master thread."""
    return not hasattr(config, "workerinput")


# ruff: noqa: E402
from ansible.module_utils.common.yaml import (  # pylint: disable=wrong-import-position
    HAS_LIBYAML,
)

if not HAS_LIBYAML:
    # While presence of libyaml is not required for runtime, we keep this error
    # fatal here in order to be sure that we spot libyaml errors during testing.
    arch = platform.machine()
    if arch not in ("arm64", "x86_64"):
        warnings.warn(
            f"This architecture ({arch}) is not supported by libyaml, performance will be degraded.",
            category=pytest.PytestWarning,
            stacklevel=1,
        )
    else:
        pytest.fail(
            "FATAL: For testing, we require pyyaml to be installed with its native extension, missing it would make testing 3x slower and risk missing essential bugs.",
        )


@pytest.fixture(name="project_path")
def fixture_project_path() -> Path:
    """Fixture to linter root folder."""
    return Path(__file__).resolve().parent
