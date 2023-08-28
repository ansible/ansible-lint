"""Implementation of partial-become rule."""
# Copyright (c) 2016 Will Thames <will@thames.id.au>
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

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule, TransformMixin

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class BecomeUserWithoutBecomeRule(AnsibleLintRule, TransformMixin):
    """become_user requires become to work as expected."""

    id = "partial-become"
    description = "``become_user`` without ``become`` will not actually change user"
    severity = "VERY_HIGH"
    tags = ["unpredictability"]
    version_added = "historic"

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        if (
            file.kind == "playbook"
            and data.get("become_user")
            and not data.get("become")
        ):
            return [
                self.create_matcherror(
                    message=self.shortdesc,
                    filename=file,
                    tag=f"{self.id}[play]",
                    lineno=data[LINE_NUMBER_KEY],
                ),
            ]
        return []

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        if task.get("become_user") and not task.get("become"):
            return [
                self.create_matcherror(
                    message=self.shortdesc,
                    filename=file,
                    tag=f"{self.id}[task]",
                    lineno=task[LINE_NUMBER_KEY],
                ),
            ]
        return []

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        if match.tag in ("partial-become[play]", "partial-become[task]"):
            target_task = self.seek(match.yaml_path, data)
            for _ in range(len(target_task)):
                k, v = target_task.popitem(False)
                if k == "become_user":
                    target_task["become"] = True
                target_task[k] = v
            match.fixed = True


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    def test_partial_become_positive() -> None:
        """Positive test for partial-become."""
        collection = RulesCollection()
        collection.register(BecomeUserWithoutBecomeRule())
        success = "examples/playbooks/rule-partial-become-without-become-pass.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_partial_become_negative() -> None:
        """Negative test for partial-become."""
        collection = RulesCollection()
        collection.register(BecomeUserWithoutBecomeRule())
        failure = "examples/playbooks/rule-partial-become-without-become-fail.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 3
