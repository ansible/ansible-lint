"""Implementation for deprecated-local-action rule."""
# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule, TransformMixin

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


class TaskNoLocalAction(AnsibleLintRule, TransformMixin):
    """Do not use 'local_action', use 'delegate_to: localhost'."""

    id = "deprecated-local-action"
    description = "Do not use ``local_action``, use ``delegate_to: localhost``"
    needs_raw_task = True
    severity = "MEDIUM"
    tags = ["deprecations"]
    version_added = "v4.0.0"

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        """Return matches for a task."""
        raw_task = task["__raw_task__"]
        if "local_action" in raw_task:
            return True

        return False

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        if match.tag == self.id:
            target_task = self.seek(match.yaml_path, data)
            for _ in range(len(target_task)):
                k, v = target_task.popitem(False)
                if k == "local_action":
                    module_name = v["module"]
                    target_task[module_name] = None
                    target_task["delegate_to"] = "localhost"
                else:
                    target_task[k] = v
        match.fixed = True


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    def test_local_action(default_rules_collection: RulesCollection) -> None:
        """Positive test deprecated_local_action."""
        results = Runner(
            "examples/playbooks/rule-deprecated-local-action-fail.yml",
            rules=default_rules_collection,
        ).run()

        assert len(results) == 1
        assert results[0].tag == "deprecated-local-action"
