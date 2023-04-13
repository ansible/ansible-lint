"""Tests related to our logging/verbosity setup."""
from __future__ import annotations

import os

import pytest

from ansiblelint.testing import run_ansible_lint


# substrs is a list of tuples, where:
#    component 1 is the substring in question
#    component 2 is whether or not to invert ("NOT") the match
@pytest.mark.parametrize(
    ("verbosity", "substrs"),
    (
        (
            "",
            [
                ("W: Listing 1 violation(s) that are fatal", False),
                ("D: ", True),
                ("I: ", True),
            ],
        ),
        (
            "-q",
            [
                ("W: ", True),
                ("D: ", True),
                ("I: ", True),
            ],
        ),
        (
            "-qq",
            [
                ("W: ", True),
                ("D: ", True),
                ("I: ", True),
            ],
        ),
        (
            "-v",
            [
                ("W: Listing 1 violation(s) that are fatal", False),
                ("ANSIBLE_LIBRARY=", False),
                ("D: ", True),
            ],
        ),
        (
            "-vv",
            [
                # ("DEBUG    Loading custom .yamllint config file,", False),
                ("W: Listing 1 violation(s) that are fatal", False),
                ("ANSIBLE_LIBRARY=", False),
                # ("DEBUG    Effective yamllint rules used", False),
            ],
        ),
        (
            "-vvvvvvvvvvvvvvvvvvvvvvvvv",
            [
                # ("DEBUG    Loading custom .yamllint config file,", False),
                ("W: Listing 1 violation(s) that are fatal", False),
                ("ANSIBLE_LIBRARY=", False),
                # ("DEBUG    Effective yamllint rules used", False),
            ],
        ),
    ),
    ids=(
        "0",  # "default-verbosity",
        "1",  # "quiet",
        "2",  # "really-quiet",
        "3",  # "loquacious",
        "4",  # "really-loquacious",
        "5",  # 'really-loquacious but with more "v"s -- same as -vv',
    ),
)
def test_default_verbosity(verbosity: str, substrs: list[tuple[str, bool]]) -> None:
    """Checks that our default verbosity displays (only) warnings."""
    # Piggyback off the .yamllint in the root of the repo, just for testing.
    # We'll "override" it with the one in the fixture, to produce a warning.
    cwd = os.path.realpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
    )

    fakerole = os.path.join("test", "fixtures", "verbosity-tests")

    if verbosity:
        result = run_ansible_lint(verbosity, fakerole, cwd=cwd)
    else:
        result = run_ansible_lint(fakerole, cwd=cwd)

    for substr, invert in substrs:
        if invert:
            assert substr not in result.stderr, result.stderr
        else:
            assert substr in result.stderr, result.stderr
