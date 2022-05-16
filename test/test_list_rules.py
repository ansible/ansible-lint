"""Tests related to our logging/verbosity setup."""

import os

import pytest

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


@pytest.mark.parametrize(
    ("result", "returncode", "format_string"),
    (
        (False, 0, "plain"),
        (False, 0, "rich"),
        (False, 0, "md"),
        (True, 2, "json"),
        (True, 2, "codeclimate"),
        (True, 2, "quiet"),
        (True, 2, "pep8"),
        (True, 2, "foo"),
    ),
    ids=(
        "plain",
        "rich",
        "md",
        "json",
        "codeclimate",
        "quiet",
        "pep8",
        "foo",
    ),
)
def test_list_rules_with_format_option(
    result: bool, returncode: int, format_string: str
) -> None:
    """Checks that listing rules with format options works."""
    # Piggyback off the .yamllint in the root of the repo, just for testing.
    # We'll "override" it with the one in the fixture.
    cwd = os.path.realpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
    )
    fakerole = os.path.join("test", "fixtures", "list-rules-tests")

    result_list_rules = run_ansible_lint("-f", format_string, "-L", fakerole, cwd=cwd)
    print(result_list_rules.stdout)

    assert (f"invalid choice: '{format_string}'" in result_list_rules.stderr) is result
    assert ("syntax-check" in result_list_rules.stdout) is not result
    assert result_list_rules.returncode is returncode


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
