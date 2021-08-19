# pylint: disable=preferred-module  # FIXME: remove once migrated per GH-725
import unittest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.OctalPermissionsRule import OctalPermissionsRule
from ansiblelint.testing import RunFromText

SUCCESS_TASKS = '''
---
- hosts: hosts
  vars:
    varset: varset
  tasks:
    - name: octal permissions test success (0600)
      file:
        path: foo
        mode: 0600

    - name: octal permissions test success (0000)
      file:
        path: foo
        mode: 0000

    - name: octal permissions test success (02000)
      file:
        path: bar
        mode: 02000

    - name: octal permissions test success (02751)
      file:
        path: bar
        mode: 02751

    - name: octal permissions test success (0777)
      file: path=baz mode=0777

    - name: octal permissions test success (0711)
      file: path=baz mode=0711

    - name:  permissions test success (0777)
      file: path=baz mode=u+rwx

    - name: octal permissions test success (777)
      file: path=baz mode=777

    - name: octal permissions test success (733)
      file: path=baz mode=733
'''

FAIL_TASKS = '''
---
- hosts: hosts
  vars:
    varset: varset
  tasks:
    - name: octal permissions test fail (600)
      file:
        path: foo
        mode: 600

    - name: octal permissions test fail (710)
      file:
        path: foo
        mode: 710

    - name: octal permissions test fail (123)
      file:
        path: foo
        mode: 123

    - name: octal permissions test fail (2000)
      file:
        path: bar
        mode: 2000
'''


class TestOctalPermissionsRuleWithFile(unittest.TestCase):

    collection = RulesCollection()
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

    def setUp(self) -> None:
        self.rule = OctalPermissionsRule()
        self.collection.register(self.rule)
        self.runner = RunFromText(self.collection)

    def test_success(self) -> None:
        results = self.runner.run_playbook(SUCCESS_TASKS)
        assert len(results) == 0

    def test_fail(self) -> None:
        results = self.runner.run_playbook(FAIL_TASKS)
        assert len(results) == 4

    def test_valid_modes(self) -> None:
        for mode in self.VALID_MODES:
            assert not self.rule.is_invalid_permission(mode), (
                "0o%o should be a valid mode" % mode
            )

    def test_invalid_modes(self) -> None:
        for mode in self.INVALID_MODES:
            assert self.rule.is_invalid_permission(mode), (
                "%d should be an invalid mode" % mode
            )
