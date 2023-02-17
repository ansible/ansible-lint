"""PyTest Fixtures."""
import importlib
import os
import subprocess
import sys

# Ensure we always run from the root of the repository
if os.getcwd() != os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))

# checking if user is running pytest without installing test dependencies:
missing = []
for module in ["ansible", "black", "flake8", "mypy", "pylint"]:
    if not importlib.util.find_spec(module):
        missing.append(module)
if missing:
    print(
        f"FATAL: Missing modules: {', '.join(missing)} -- probably you missed installing test requirements with: pip install -e '.[test]'",
        file=sys.stderr,
    )
    sys.exit(1)
# we need to be sure that we have the requirements installed as some tests
# might depend on these. This approach is compatible with GHA caching.
try:
    subprocess.check_output(
        ["./tools/install-reqs.sh"],
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

if not HAS_LIBYAML:
    # While presence of libyaml is not required for runtime, we keep this error
    # fatal here in order to be sure that we spot libyaml errors during testing.
    print(
        "FATAL: For testing, we require pyyaml to be installed with its native extension, missing it would make testing 3x slower and risk missing essential bugs.",
        file=sys.stderr,
    )
    sys.exit(1)


os.environ["NO_COLOR"] = "1"
