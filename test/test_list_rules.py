"""Tests related to our logging/verbosity setup."""

import os

from ansiblelint.testing import run_ansible_lint


def test_list_rules_includes_opt_in_rules() -> None:
    """Checks that listing rules also includes the opt-in rules."""
    # Piggyback off the .yamllint in the root of the repo, just for testing.
    # We'll "override" it with the one in the fixture.
    cwd = os.path.realpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
    )
    fakerole = os.path.join("test", "fixtures", "list-rules-tests")

    result_list_rules = run_ansible_lint("-L", fakerole, cwd=cwd)

    assert ("opt-in" in result_list_rules.stdout) is True


def test_list_tags_includes_opt_in_rules() -> None:
    """Checks that listing tags also includes the opt-in rules."""
    # Piggyback off the .yamllint in the root of the repo, just for testing.
    # We'll "override" it with the one in the fixture.
    cwd = os.path.realpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
    )
    fakerole = os.path.join("test", "fixtures", "list-rules-tests")

    result_list_tags = run_ansible_lint("-L", fakerole, cwd=cwd)

    assert ("opt-in" in result_list_tags.stdout) is True
