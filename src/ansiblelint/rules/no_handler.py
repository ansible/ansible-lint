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

"""UseHandlerRatherThanWhenChangedRule used with ansible-lint."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.utils import Task

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


def _changed_in_when(item: str) -> bool:
    if not isinstance(item, str):
        return False
    item_list = item.split()

    if {"and", "or", "not"} & set(item_list):
        return False
    return any(
        changed in item
        for changed in [
            ".changed",
            "|changed",
            '["changed"]',
            "['changed']",
            "is changed",
        ]
    )


class UseHandlerRatherThanWhenChangedRule(AnsibleLintRule, TransformMixin):
    """Tasks that run when changed should likely be handlers."""

    id = "no-handler"
    description = (
        "If a task has a ``when: result.changed`` setting, it is effectively "
        "acting as a handler. You could use ``notify`` and move that task to "
        "``handlers``."
    )
    link = "https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_handlers.html#handlers"
    severity = "MEDIUM"
    tags = ["idiom"]
    version_added = "historic"

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        if task["__ansible_action_type__"] != "task" or task.is_handler():
            return False

        when = task.get("when")
        result = False

        if isinstance(when, list):
            if len(when) <= 1:
                result = _changed_in_when(when[0])
        elif isinstance(when, str):
            result = _changed_in_when(when)
        return result

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        """Move the task to 'handler'.

        Also, adds 'notify' to the task which
        wants to run the handler.
        """
        if match.tag == self.id and isinstance(data, CommentedSeq):
            is_fixed: bool = False
            task_name = None
            when_val = None
            if isinstance(match.task, Task):
                task_name = str(match.task.get("name"))
                when = match.task.get("when")
                # looks for the variable used as the value of when clause
                if isinstance(when, list) and len(when) <= 1:
                    when_val = when[0].split(".")[0]
                elif isinstance(when, str):
                    when_val = when.split(".")[0]

            for item in data:
                # Item is a play
                # Look for handlers at the play level
                if "handlers" not in item:
                    item["handlers"] = CommentedSeq()
                for k, v in enumerate(item.get("tasks")):
                    # As there can be more than one tasks
                    # Check if 'register' is in task
                    # and if it's value is same as that of the
                    # 'when' clause of the task (which is to be moved to the handler).

                    # Need to fix scenario mentioned by Brad
                    if "register" in v and v["register"] == when_val:
                        # Add notify to the task
                        if "notify" not in v:
                            notify_seq = CommentedSeq()

                        # if value of notify is a string
                        elif not isinstance(v["notify"], CommentedSeq):
                            old_val = v["notify"]
                            notify_seq = CommentedSeq()
                            notify_seq.append(old_val)
                        notify_seq.append(task_name)

                        res = clean_comment(v.ca.items)
                        for key, value in res.items():
                            if not value.get("val", None):
                                v.ca.items.pop(key)
                            elif value.get("move"):
                                item.get("tasks").yaml_set_comment_before_after_key(
                                    k + 1, value.get("val")
                                )
                            else:
                                v.ca.items[key][2].value = value.get("val", None)

                        v.insert(len(v), "notify", notify_seq)

                    if v["name"] == task_name:
                        item["handlers"].append(item.get("tasks").pop(k))
                        is_fixed = True

            if is_fixed:
                match.fixed = True


def clean_comment(comments: dict[str, Any]) -> dict[str, Any]:
    r"""Clean comments and return values without \n."""
    res = {}
    for key, comment in comments.items():
        move_comment_to_next_task = False
        # Check if comment is on a new line
        if "\n\n" in comment[2].value[0:2]:
            move_comment_to_next_task = True

        before, _, after = comment[2].value.partition("\n")

        if move_comment_to_next_task and after:
            after = after.strip()
            res[key] = {
                "val": after if after else None,
                "move": move_comment_to_next_task,
            }
        if before:
            before = before.strip()
            res[key] = {
                "val": before if before else None,
                "move": move_comment_to_next_task,
            }
    return res


if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param("examples/playbooks/no_handler_fail.yml", 5, id="fail"),
            pytest.param("examples/playbooks/no_handler_pass.yml", 0, id="pass"),
        ),
    )
    def test_no_handler(
        default_rules_collection: RulesCollection,
        test_file: str,
        failures: int,
    ) -> None:
        """Test rule matches."""
        results = Runner(test_file, rules=default_rules_collection).run()
        assert len(results) == failures
        for result in results:
            assert result.tag == "no-handler"
