"""PyTest Fixtures."""
import os
import re
import sys
from typing import List

os.environ["NO_COLOR"] = "1"
pytest_plugins = ["ansiblelint.testing.fixtures"]


def pytest_cmdline_preparse(args: List[str]) -> None:
    """Pytest hook."""
    # disable xdist when called with -k args (filtering)
    # https://stackoverflow.com/questions/66407583/how-to-disable-pytest-xdist-only-when-pytest-is-called-with-filters
    if "xdist" in sys.modules and "-k" in args:
        for i, arg in enumerate(args):
            # remove -n # option
            if arg == "-n":
                del args[i]
                del args[i]
                break
            # remove -n# option
            if re.match(r"-n\d+", arg):
                del args[i]
                break

        args[:] = ["-n0"] + args
