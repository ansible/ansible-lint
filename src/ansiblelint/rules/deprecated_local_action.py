"""Implementation for deprecated-local-action rule."""

# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import copy
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.runner import get_matches
from ansiblelint.transformer import Transformer

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from ansiblelint.config import Options
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.utils import Task


_logger = logging.getLogger(__name__)


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
            # we do not want perform a partial modification accidentally
            original_target_task = self.seek(match.yaml_path, data)
            target_task = copy.deepcopy(original_target_task)
            for _ in range(len(target_task)):
                k, v = target_task.popitem(False)
                if k == "local_action":
                    if isinstance(v, dict):
                        module_name = v["module"]
                        target_task[module_name] = None
                        target_task["delegate_to"] = "localhost"
                    elif isinstance(v, str):
                        module_name, module_value = v.split(" ", 1)
                        target_task[module_name] = module_value
                        target_task["delegate_to"] = "localhost"
                    else:
                        _logger.debug(
                            "Ignored unexpected data inside %s transform.",
                            self.id,
                        )
                        return
                else:
                    target_task[k] = v
        match.fixed = True
        original_target_task.clear()
        original_target_task.update(target_task)


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    from unittest import mock

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_local_action(default_rules_collection: RulesCollection) -> None:
        """Positive test deprecated_local_action."""
        results = Runner(
            "examples/playbooks/rule-deprecated-local-action-fail.yml",
            rules=default_rules_collection,
        ).run()

        assert len(results) == 1
        assert results[0].tag == "deprecated-local-action"

    @mock.patch.dict(os.environ, {"ANSIBLE_LINT_WRITE_TMP": "1"}, clear=True)
    def test_local_action_transform(
        config_options: Options,
        default_rules_collection: RulesCollection,
    ) -> None:
        """Test transform functionality for no-log-password rule."""
        playbook = Path("examples/playbooks/tasks/local_action.yml")
        config_options.write_list = ["all"]

        config_options.lintables = [str(playbook)]
        runner_result = get_matches(
            rules=default_rules_collection,
            options=config_options,
        )
        transformer = Transformer(result=runner_result, options=config_options)
        transformer.run()
        matches = runner_result.matches
        assert len(matches) == 3

        orig_content = playbook.read_text(encoding="utf-8")
        expected_content = playbook.with_suffix(
            f".transformed{playbook.suffix}",
        ).read_text(encoding="utf-8")
        transformed_content = playbook.with_suffix(f".tmp{playbook.suffix}").read_text(
            encoding="utf-8",
        )

        assert orig_content != transformed_content
        assert expected_content == transformed_content
        playbook.with_suffix(f".tmp{playbook.suffix}").unlink()
