"""Implementation for deprecated-local-action rule."""

# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ruamel.yaml.comments import CommentedMap

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.runner import get_matches
from ansiblelint.transformer import Transformer

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedSeq

    from ansiblelint.config import Options
    from ansiblelint.utils import Task


_logger = logging.getLogger(__name__)


class LocalActionTransformError(Exception):
    """Exception raised when a local_action is not processed correctly."""

    def __init__(self, message: str) -> None:
        """Initialize the LocalActionTransformError with a message."""
        _logger.error(message)


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
        try:
            self.perform_transform(match, lintable, data)
        except LocalActionTransformError as e:
            match.fixed = False
            match.message = str(e)
            return

    def perform_transform(
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

        Raises:
            LocalActionTransformError: If the local_action is not dict | str.
        """
        original_task = self.seek(match.yaml_path, data)
        task_location = f"{lintable.name}:{match.lineno}"

        target_task = {}

        for k, v in original_task.items():
            if k == "local_action":
                if isinstance(v, dict):
                    target_task.update(self.process_dict(v, task_location))
                elif isinstance(v, str):
                    target_task.update(self.process_string(v, task_location))
                else:
                    err = f"Unsupported local_action type '{type(v).__name__}' in task at {task_location}"
                    raise LocalActionTransformError(err)
                target_task["delegate_to"] = "localhost"
            else:
                target_task[k] = v

        match.fixed = True
        original_task.clear()
        original_task.update(target_task)

    def process_dict(
        self, local_action: dict[str, Any], task_location: str
    ) -> dict[str, Any]:
        """Process a dict-form local_action.

        Args:
            local_action: The local_action dictionary.
            task_location: The location of the task.

        Returns:
            A dictionary with the module and parameters.

        Raises:
            LocalActionTransformError: If the local_action dictionary is missing a 'module' key.
        """
        if "module" not in local_action:
            err = f"No 'module' key in local_action in task at {task_location}"
            raise LocalActionTransformError(err)
        return {
            local_action["module"]: {
                k: v for k, v in local_action.items() if k != "module"
            }
            or None
        }

    def process_string(
        self, local_action: str, task_location: str
    ) -> dict[str, str | None]:
        """Process a string-form local_action.

        Args:
            local_action: The local_action string.
            task_location: The location of the task.

        Returns:
            A dictionary with the module and parameters.

        Raises:
            LocalActionTransformError: If the local_action string is empty or whitespace.
        """
        if not local_action or not local_action.strip():
            err = f"Empty local_action string in task at {task_location}"
            raise LocalActionTransformError(err)
        parts = local_action.split(" ", 1)
        return {parts[0]: parts[1] if len(parts) > 1 else None}


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_local_action(default_rules_collection: RulesCollection) -> None:
        """Positive test deprecated_local_action."""
        results = Runner(
            "examples/playbooks/rule-deprecated-local-action-fail.yml",
            rules=default_rules_collection,
        ).run()

        assert any(result.tag == "deprecated-local-action" for result in results)

    @pytest.mark.parametrize(
        ("data", "prefix"),
        (
            (
                CommentedMap({"local_action": True}),
                "Unsupported local_action type 'bool'",
            ),
            (
                CommentedMap({"local_action": 123}),
                "Unsupported local_action type 'int'",
            ),
            (
                CommentedMap({"local_action": 12.34}),
                "Unsupported local_action type 'float'",
            ),
            (
                CommentedMap({"local_action": []}),
                "Unsupported local_action type 'list'",
            ),
            (CommentedMap({"local_action": {}}), "No 'module' key in local_action"),
            (CommentedMap({"local_action": ""}), "Empty local_action string"),
            (CommentedMap({"local_action": "  "}), "Empty local_action string"),
        ),
        ids=[
            "bool",
            "int",
            "float",
            "list",
            "empty_dict",
            "empty_string",
            "whitespace_string",
        ],
    )
    def test_local_action_transform_fail(
        caplog: pytest.LogCaptureFixture, data: CommentedMap, prefix: str
    ) -> None:
        """Test transform functionality for a failure.

        Args:
            caplog: The pytest fixture for capturing logs.
            data: The data to test.
            prefix: The expected error prefix.
        """
        file = "site.yml"
        rule = TaskNoLocalActionRule()
        lintable = Lintable(name=file)
        match_error = MatchError(message="error", lintable=lintable, lineno=1)
        with pytest.raises(LocalActionTransformError):
            rule.perform_transform(match_error, lintable, data)
        assert f"{prefix} in task at {file}:1" in caplog.text

    def test_local_action_transform(
        config_options: Options,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test transform functionality for no-log-password rule."""
        monkeypatch.setenv("ANSIBLE_LINT_WRITE_TMP", "1")

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
