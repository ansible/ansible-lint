"""Implementation of risky-octal rule."""
# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule, RulesCollection
from ansiblelint.runner import Runner

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class OctalPermissionsRule(AnsibleLintRule):
    """Octal file permissions must contain leading zero or be a string."""

    id = "risky-octal"
    description = (
        "Numeric file permissions without leading zero can behave "
        "in unexpected ways."
    )
    link = "https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html"
    severity = "VERY_HIGH"
    tags = ["formatting"]
    version_added = "historic"

    _modules = [
        "assemble",
        "copy",
        "file",
        "ini_file",
        "lineinfile",
        "replace",
        "synchronize",
        "template",
        "unarchive",
    ]

    @staticmethod
    def is_invalid_permission(mode: int) -> bool:
        """Check if permissions are valid.

        Sensible file permission modes don't have write bit set when read bit
        is not set and don't have execute bit set when user execute bit is
        not set.

        Also, user permissions are more generous than group permissions and
        user and group permissions are more generous than world permissions.
        """
        other_write_without_read = (
            mode % 8 and mode % 8 < 4 and not (mode % 8 == 1 and (mode >> 6) % 2 == 1)
        )
        group_write_without_read = (
            (mode >> 3) % 8
            and (mode >> 3) % 8 < 4
            and not ((mode >> 3) % 8 == 1 and (mode >> 6) % 2 == 1)
        )
        user_write_without_read = (
            (mode >> 6) % 8 and (mode >> 6) % 8 < 4 and not (mode >> 6) % 8 == 1
        )
        other_more_generous_than_group = mode % 8 > (mode >> 3) % 8
        other_more_generous_than_user = mode % 8 > (mode >> 6) % 8
        group_more_generous_than_user = (mode >> 3) % 8 > (mode >> 6) % 8

        return bool(
            other_write_without_read
            or group_write_without_read
            or user_write_without_read
            or other_more_generous_than_group
            or other_more_generous_than_user
            or group_more_generous_than_user
        )

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str:
        if task["action"]["__ansible_module__"] in self._modules:
            mode = task["action"].get("mode", None)

            if isinstance(mode, str):
                return False

            if isinstance(mode, int) and self.is_invalid_permission(mode):
                return f'`mode: {mode}` should have a string value with leading zero `mode: "0{mode:o}"` or use symbolic mode.'
        return False


if "pytest" in sys.modules:
    import pytest

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

    @pytest.mark.parametrize(
        ("file", "failures"),
        (
            pytest.param("examples/playbooks/rule-risky-octal-pass.yml", 0, id="pass"),
            pytest.param("examples/playbooks/rule-risky-octal-fail.yml", 4, id="fail"),
        ),
    )
    def test_octal(file: str, failures: int) -> None:
        """Test that octal permissions are valid."""
        collection = RulesCollection()
        collection.register(OctalPermissionsRule())
        results = Runner(file, rules=collection).run()
        assert len(results) == failures
        for result in results:
            assert result.rule.id == "risky-octal"

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
            assert rule.is_invalid_permission(
                mode
            ), f"{mode:d} should be an invalid mode"
