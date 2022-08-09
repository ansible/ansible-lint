"""Tests for risky-octal rule."""
import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.risky_octal import OctalPermissionsRule
from ansiblelint.testing import RunFromText

SUCCESS_TASKS = """
---
- hosts: hosts
  vars:
    varset: varset
  tasks:
    - name: Octal permissions test success (0600)
      file:
        path: foo
        mode: 0600

    - name: Octal permissions test success (0000)
      file:
        path: foo
        mode: 0000

    - name: Octal permissions test success (02000)
      file:
        path: bar
        mode: 02000

    - name: Octal permissions test success (02751)
      file:
        path: bar
        mode: 02751

    - name: Octal permissions test success (0777)
      file: path=baz mode=0777

    - name: Octal permissions test success (0711)
      file: path=baz mode=0711

    - name: Permissions test success (0777)
      file: path=baz mode=u+rwx

    - name: Octal permissions test success (777)
      file: path=baz mode=777

    - name: Octal permissions test success (733)
      file: path=baz mode=733
"""

FAIL_TASKS = """
---
- hosts: hosts
  vars:
    varset: varset
  tasks:
    - name: Octal permissions test fail (600)
      file:
        path: foo
        mode: 600

    - name: Octal permissions test fail (710)
      file:
        path: foo
        mode: 710

    - name: Octal permissions test fail (123)
      file:
        path: foo
        mode: 123

    - name: Octal permissions test fail (2000)
      file:
        path: bar
        mode: 2000
"""


VALID_MODES = [
    0o777,
    0o775,
    0o770,
    0o755,
    0o750,
    0o711,
    0o710,
    0o700,
    0o666,
    0o664,
    0o660,
    0o644,
    0o640,
    0o600,
    0o555,
    0o551,
    0o550,
    0o511,
    0o510,
    0o500,
    0o444,
    0o440,
    0o400,
]

INVALID_MODES = [
    777,
    775,
    770,
    755,
    750,
    711,
    710,
    700,
    666,
    664,
    660,
    644,
    640,
    622,
    620,
    600,
    555,
    551,
    550,  # 511 == 0o777, 510 == 0o776, 500 == 0o764
    444,
    440,
    400,
]


@pytest.fixture(name="runner")
def fixture_runner() -> RunFromText:
    """Fixture for testing the OctalPermissionsRule."""
    collection = RulesCollection()
    rule = OctalPermissionsRule()
    collection.register(rule)
    return RunFromText(collection)


def test_octal_success(runner: RunFromText) -> None:
    """Test that octal permissions are valid."""
    results = runner.run_playbook(SUCCESS_TASKS)
    assert len(results) == 0


def test_octal_fail(runner: RunFromText) -> None:
    """Test that octal permissions are invalid."""
    results = runner.run_playbook(FAIL_TASKS)
    assert len(results) == 4


def test_octal_valid_modes() -> None:
    """Test that octal modes are valid."""
    rule = OctalPermissionsRule()
    for mode in VALID_MODES:
        assert not rule.is_invalid_permission(
            mode
        ), f"0o{mode:o} should be a valid mode"


def test_octal_invalid_modes() -> None:
    """Test that octal modes are invalid."""
    rule = OctalPermissionsRule()
    for mode in INVALID_MODES:
        assert rule.is_invalid_permission(mode), f"{mode:d} should be an invalid mode"
