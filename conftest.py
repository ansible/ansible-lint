"""PyTest Fixtures."""
import importlib
import os
import subprocess
import sys
from typing import Any

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
    from ansible_compat.prerun import get_cache_dir

    cache_dir = get_cache_dir(".")
    subprocess.check_output(
        [
            "ansible-galaxy",
            "collection",
            "install",
            "-p",
            f"{cache_dir}/collections",
            "-r",
            "requirements.yml",
        ],
        stderr=subprocess.PIPE,
        text=True,
    )
except subprocess.CalledProcessError as exc:
    print(f"{exc}\n{exc.stderr}\n{exc.stdout}", file=sys.stderr)
    sys.exit(1)

# flake8: noqa: E402
from ansible.module_utils.common.yaml import (  # pylint: disable=wrong-import-position
    HAS_LIBYAML,
)

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
