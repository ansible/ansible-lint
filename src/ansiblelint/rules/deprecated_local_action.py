"""Implementation for deprecated-local-action rule."""

# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import logging
import os
import shlex
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


class TaskNoLocalActionRule(AnsibleLintRule, TransformMixin):
    """Do not use 'local_action', use 'delegate_to: localhost'."""

    id = "deprecated-local-action"
    description = "Do not use ``local_action``, use ``delegate_to: localhost``"
    needs_raw_task = True
    severity = "MEDIUM"
    tags = ["deprecations"]
    version_changed = "4.0.0"

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str:
        """Return matches for a task."""
        raw_task = task["__raw_task__"]
        return "local_action" in raw_task

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        """Transform the task to use delegate_to: localhost.

        Args:
            match: The match object.
            lintable: The lintable object.
            data: The data to transform.
        """
        original_task = self.seek(match.yaml_path, data)
        if not isinstance(original_task, dict):
            msg = f"Ignored unexpected data inside {getattr(match, 'id', 'unknown')} transform: not a dict."
            _logger.debug(msg)
            return

        if "local_action" not in original_task:
            return

        # Copy all keys except "local_action"
        target_task = {}

        # task name first
        if name := original_task.pop("name", None):
            target_task["name"] = name

        local_action = original_task.pop("local_action")

        # Handle dict-form local_action
        if isinstance(local_action, dict):
            if "module" not in local_action:
                msg = f"No 'module' key in local_action dict for task {getattr(match, 'id', 'unknown')}"
                _logger.warning(msg)
                return
            plugin_details = {k: v for k, v in local_action.items() if k != "module"}
            target_task[local_action["module"]] = (
                plugin_details if plugin_details else None
            )

        # Handle string-form local_action
        elif isinstance(local_action, str):
            try:
                tokens = shlex.split(local_action)
            except ValueError as exc:
                msg = f"Failed to split local_action string for task {getattr(match, 'id', 'unknown')}: {exc}"
                _logger.warning(msg)
                return

            if not tokens:
                msg = f"Empty local_action string for task {getattr(match, 'id', 'unknown')}"
                _logger.warning(msg)
                return

            plugin, *args = tokens

            # If all args are key=value, build a dict
            if args and all("=" in a for a in args):
                dict_params = {}
                for a in args:
                    k, v = a.split("=", 1)
                    dict_params[k] = v
                target_task[plugin] = dict_params
            # Otherwise, treat as positional arguments (join into a single string, if present)
            elif args:
                string_params = " ".join(args) if len(args) > 1 else args[0]
                target_task[plugin] = string_params
            else:
                target_task[plugin] = None

        else:
            msg = f"Unsupported local_action type ({type(local_action)}) in task {getattr(match, 'id', 'unknown')}"
            _logger.warning(msg)
            return

        # Copy over all other keys
        target_task.update(original_task)
        target_task["delegate_to"] = "localhost"

        match.fixed = True
        original_task.clear()
        original_task.update(target_task)


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

        assert any(result.tag == "deprecated-local-action" for result in results)

    @mock.patch.dict(os.environ, {"ANSIBLE_LINT_WRITE_TMP": "1"}, clear=True)
    def test_local_action_transform(
        config_options: Options,
    ) -> None:
        """Test transform functionality for no-log-password rule."""
        playbook = Path("examples/playbooks/tasks/local_action.yml")
        config_options.write_list = ["all"]

        config_options.lintables = [str(playbook)]
        only_local_action_rule: RulesCollection = RulesCollection()
        only_local_action_rule.register(TaskNoLocalActionRule())
        runner_result = get_matches(
            rules=only_local_action_rule,
            options=config_options,
        )
        transformer = Transformer(result=runner_result, options=config_options)
        transformer.run()
        matches = runner_result.matches
        assert any(error.tag == "deprecated-local-action" for error in matches)

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
