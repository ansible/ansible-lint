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

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.constants import LINE_NUMBER_KEY
from ansiblelint.rules import AnsibleLintRule, TransformMixin

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class BecomeUserWithoutBecomeRule(AnsibleLintRule, TransformMixin):
    """``become_user`` should have a corresponding ``become`` at the play or task level."""

    id = "partial-become"
    description = "``become_user`` should have a corresponding ``become`` at the play or task level."
    severity = "VERY_HIGH"
    tags = ["unpredictability"]
    version_added = "historic"

    def matchplay(
        self: BecomeUserWithoutBecomeRule,
        file: Lintable,
        data: dict[str, Any],
    ) -> list[MatchError]:
        """Match become_user without become in play.

        :param file: The file to lint.
        :param data: The data to lint (play)
        :returns: A list of errors.
        """
        if file.kind != "playbook":
            return []
        errors = []
        partial = "become_user" in data and "become" not in data
        if partial:
            error = self.create_matcherror(
                message=self.shortdesc,
                filename=file,
                tag=f"{self.id}[play]",
                lineno=data[LINE_NUMBER_KEY],
            )
            errors.append(error)
        return errors

    def matchtask(
        self: BecomeUserWithoutBecomeRule,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        """Match become_user without become in task.

        :param task: The task to lint.
        :param file: The file to lint.
        :returns: A list of errors.
        """
        data = task.normalized_task
        errors = []
        partial = "become_user" in data and "become" not in data
        if partial:
            error = self.create_matcherror(
                message=self.shortdesc,
                filename=file,
                tag=f"{self.id}[task]",
                lineno=task[LINE_NUMBER_KEY],
            )
            errors.append(error)
        return errors

    def _dive(self: BecomeUserWithoutBecomeRule, data: CommentedSeq) -> Iterator[Any]:
        """Dive into the data and yield each item.

        :param data: The data to dive into.
        :yield: Each item in the data.
        """
        for item in data:
            for nested in ("block", "rescue", "always"):
                if nested in item:
                    yield from self._dive(item[nested])
            yield item

    def transform(
        self: BecomeUserWithoutBecomeRule,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        """Transform the data.

        :param match: The match to transform.
        :param lintable: The file to transform.
        :param data: The data to transform.
        """
        if not isinstance(data, CommentedSeq):
            return

        obj = self.seek(match.yaml_path, data)
        if "become" in obj and "become_user" in obj:
            match.fixed = True
            return
        if "become" not in obj and "become_user" not in obj:
            match.fixed = True
            return

        self._transform_plays(plays=data)

        if "become" in obj and "become_user" in obj:
            match.fixed = True
            return
        if "become" not in obj and "become_user" not in obj:
            match.fixed = True
            return

    def is_ineligible_for_transform(
        self: BecomeUserWithoutBecomeRule,
        data: CommentedMap,
    ) -> bool:
        """Check if the data is eligible for transformation.

        :param data: The data to check.
        :returns: True if ineligible, False otherwise.
        """
        if any("include" in key for key in data):
            return True
        if "notify" in data:
            return True
        return False

    def _transform_plays(self, plays: CommentedSeq) -> None:
        """Transform the plays.

        :param plays: The plays to transform.
        """
        for play in plays:
            self._transform_play(play=play)

    def _transform_play(self, play: CommentedMap) -> None:
        """Transform the play.

        :param play: The play to transform.
        """
        # Ensure we have no includes in this play
        task_groups = ("tasks", "pre_tasks", "post_tasks", "handlers")
        for task_group in task_groups:
            tasks = self._dive(play.get(task_group, []))
            for task in tasks:
                if self.is_ineligible_for_transform(task):
                    return
        remove_play_become_user = False
        for task_group in task_groups:
            tasks = self._dive(play.get(task_group, []))
            for task in tasks:
                b_in_t = "become" in task
                bu_in_t = "become_user" in task
                b_in_p = "become" in play
                bu_in_p = "become_user" in play
                if b_in_t and not bu_in_t and bu_in_p:
                    # Preserve the end comment if become is the last key
                    comment = None
                    if list(task.keys())[-1] == "become" and "become" in task.ca.items:
                        comment = task.ca.items.pop("become")
                    become_index = list(task.keys()).index("become")
                    task.insert(become_index + 1, "become_user", play["become_user"])
                    if comment:
                        self._attach_comment_end(task, comment)
                    remove_play_become_user = True
                if bu_in_t and not b_in_t and b_in_p:
                    become_user_index = list(task.keys()).index("become_user")
                    task.insert(become_user_index, "become", play["become"])
                if bu_in_t and not b_in_t and not b_in_p:
                    # Preserve the end comment if become_user is the last key
                    comment = None
                    if (
                        list(task.keys())[-1] == "become_user"
                        and "become_user" in task.ca.items
                    ):
                        comment = task.ca.items.pop("become_user")
                    task.pop("become_user")
                    if comment:
                        self._attach_comment_end(task, comment)
        if remove_play_become_user:
            del play["become_user"]

    def _attach_comment_end(
        self,
        obj: CommentedMap | CommentedSeq,
        comment: Any,
    ) -> None:
        """Attach a comment to the end of the object.

        :param obj: The object to attach the comment to.
        :param comment: The comment to attach.
        """
        if isinstance(obj, CommentedMap):
            last = list(obj.keys())[-1]
            if not isinstance(obj[last], CommentedSeq | CommentedMap):
                obj.ca.items[last] = comment
                return
            self._attach_comment_end(obj[last], comment)
        elif isinstance(obj, CommentedSeq):
            if not isinstance(obj[-1], CommentedSeq | CommentedMap):
                obj.ca.items[len(obj)] = comment
                return
            self._attach_comment_end(obj[-1], comment)


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_partial_become_pass() -> None:
        """No errors found for partial-become."""
        collection = RulesCollection()
        collection.register(BecomeUserWithoutBecomeRule())
        success = "examples/playbooks/rule-partial-become-without-become-pass.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_partial_become_fail() -> None:
        """Errors found for partial-become."""
        collection = RulesCollection()
        collection.register(BecomeUserWithoutBecomeRule())
        failure = "examples/playbooks/rule-partial-become-without-become-fail.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 3
