import os.path

import pytest

from ansiblelint.testing import run_ansible_lint


@pytest.mark.parametrize(
    ("role", "expect_warning"),
    (
        ("template_lookup", False),
        ("template_lookup_missing", True),
    ),
)
def test_template_lookup(role: str, expect_warning: bool) -> None:
    role_path = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "examples", "roles", role
        )
    )
    result = run_ansible_lint("-v", role_path)
    assert ("Unable to find" in result.stderr) == expect_warning
