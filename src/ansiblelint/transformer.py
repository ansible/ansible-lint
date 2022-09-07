"""Transformer implementation."""
from __future__ import annotations

import logging
from argparse import Namespace
from typing import Any, Union, cast

from ansible.template import Templar
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.constants import NESTED_TASK_KEYS, PLAYBOOK_TASK_KEYWORDS
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.jinja_utils.yaml_string import JinjaTemplate
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.runner import LintResult
from ansiblelint.utils import PLAYBOOK_DIR, ansible_templar
from ansiblelint.yaml_utils import FormattedYAML, get_path_to_play, get_path_to_task

__all__ = ["Transformer"]

_logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class Transformer:
    """Transformer class marshals transformations.

    The Transformer is similar to the ``ansiblelint.runner.Runner`` which manages
    running each of the rules. We only expect there to be one ``Transformer`` instance
    which should be instantiated from the main entrypoint function.

    In the future, the transformer will be responsible for running transforms for each
    of the rule matches. For now, it just reads/writes YAML files which is a
    pre-requisite for the planned rule-specific transforms.
    """

    def __init__(self, result: LintResult, options: Namespace):
        """Initialize a Transformer instance."""
        self.write_set = self.effective_write_set(options.write_list)

        self.matches: list[MatchError] = result.matches
        self.files: set[Lintable] = result.files

        file: Lintable
        # pylint: disable=undefined-variable
        lintables: dict[str, Lintable] = {file.filename: file for file in result.files}
        self.matches_per_file: dict[Lintable, list[MatchError]] = {
            file: [] for file in result.files
        }

        for match in self.matches:
            try:
                lintable = lintables[match.filename]
            except KeyError:
                # we shouldn't get here, but this is easy to recover from so do that.
                lintable = Lintable(match.filename)
                self.matches_per_file[lintable] = []
            self.matches_per_file[lintable].append(match)

    @staticmethod
    def effective_write_set(write_list: list[str]) -> set[str]:
        """Simplify write_list based on ``"none"`` and ``"all"`` keywords.

        ``"none"`` resets the enabled rule transforms.
        This returns ``{"none"}`` or a set of everything after the last ``"none"``.

        If ``"all"`` is in the ``write_list`` (after ``"none"`` if present),
        then this will return ``{"all"}``.
        """
        none_indexes = [i for i, value in enumerate(write_list) if value == "none"]
        if none_indexes:
            index = none_indexes[-1]
            if len(write_list) > index + 1:
                index += 1
            write_list = write_list[index:]
        if "all" in write_list:
            return {"all"}
        return set(write_list)

    def run(self) -> None:
        """For each file, read it, execute transforms on it, then write it."""
        for file, matches in self.matches_per_file.items():
            # str() convinces mypy that "text/yaml" is a valid Literal.
            # Otherwise, it thinks base_kind is one of playbook, meta, tasks, ...
            file_is_yaml = str(file.base_kind) == "text/yaml"

            try:
                data: str = file.content
            except (UnicodeDecodeError, IsADirectoryError):
                # we hit a binary file (eg a jar or tar.gz) or a directory
                data = ""
                file_is_yaml = False

            ruamel_data: CommentedMap | CommentedSeq | None = None
            if file_is_yaml:
                # We need a fresh YAML() instance for each load because ruamel.yaml
                # stores intermediate state during load which could affect loading
                # any other files. (Based on suggestion from ruamel.yaml author)
                yaml = FormattedYAML()

                ruamel_data = yaml.loads(data)
                if not isinstance(ruamel_data, (CommentedMap, CommentedSeq)):
                    # This is an empty vars file or similar which loads as None.
                    # It is not safe to write this file or data-loss is likely.
                    # Only maps and sequences can preserve comments. Skip it.
                    continue
                self._process_jinja_in_yaml(file, ruamel_data)

            if self.write_set != {"none"}:
                self._do_transforms(file, ruamel_data or data, file_is_yaml, matches)

            if file_is_yaml:
                # noinspection PyUnboundLocalVariable
                file.content = yaml.dumps(ruamel_data)

            if file.updated:
                file.write()

    def _do_transforms(
        self,
        file: Lintable,
        data: CommentedMap | CommentedSeq | str,
        file_is_yaml: bool,
        matches: list[MatchError],
    ) -> None:
        """Do Rule-Transforms handling any last-minute MatchError inspections."""
        for match in sorted(matches):
            if not isinstance(match.rule, TransformMixin):
                continue
            if self.write_set != {"all"}:
                rule = cast(AnsibleLintRule, match.rule)
                rule_definition = set(rule.tags)
                rule_definition.add(rule.id)
                if rule_definition.isdisjoint(self.write_set):
                    # rule transform not requested. Skip it.
                    continue
            if file_is_yaml and not match.yaml_path:
                data = cast(Union[CommentedMap, CommentedSeq], data)
                if match.match_type == "play":
                    match.yaml_path = get_path_to_play(file, match.linenumber, data)
                elif match.task or file.kind in (
                    "tasks",
                    "handlers",
                    "playbook",
                ):
                    match.yaml_path = get_path_to_task(file, match.linenumber, data)
            match.rule.transform(match, file, data)

    def _process_jinja_in_yaml(
        self, file: Lintable, ruamel_data: CommentedMap | CommentedSeq
    ) -> None:
        """Iterate over the yaml document to turn jinja templates into JinjaTemplate.

        This modifies the ruamel_data in place.
        """
        if file.kind not in ("playbook", "tasks", "handlers", "vars", "inventory"):
            return

        # each JinjaTemplate instance in a file will use the same jinja_env
        basedir = file.path.parent
        template_vars = dict(playbook_dir=PLAYBOOK_DIR or basedir.absolute())
        templar = ansible_templar(basedir=str(basedir), templatevars=template_vars)

        if isinstance(ruamel_data, CommentedSeq):
            if file.kind == "playbook":  # a playbook is a list of plays
                self._process_jinja_in_playbook(templar, ruamel_data)
            elif file.kind in ("tasks", "handlers"):
                self._process_jinja_in_tasks_block(templar, ruamel_data)
        elif isinstance(ruamel_data, CommentedMap):
            if file.kind == "vars":
                self._process_jinja_in_vars_block(templar, ruamel_data)
            elif file.kind == "inventory":
                self._process_jinja_in_inventory(templar, ruamel_data)

    def _process_jinja_in_playbook(
        self, templar: Templar, ruamel_data: CommentedSeq
    ) -> None:
        play: CommentedMap
        for play in ruamel_data:
            for key, value in play.items():
                if key in PLAYBOOK_TASK_KEYWORDS:
                    self._process_jinja_in_tasks_block(templar, value)
                elif key == "roles":
                    self._process_jinja_in_roles_block(templar, value)
                elif key == "vars":
                    self._process_jinja_in_vars_block(templar, value)
                elif key == "when":
                    play[key] = self._process_jinja_value(templar, value, implicit=True)
                else:
                    play[key] = self._process_jinja_value(templar, value)

    def _process_jinja_in_roles_block(
        self, templar: Templar, ruamel_data: CommentedSeq
    ) -> None:
        role: CommentedMap | str
        for role in ruamel_data:
            if not isinstance(role, CommentedMap):
                continue
            for key, value in role.items():
                if key == "vars":
                    self._process_jinja_in_vars_block(templar, value)
                elif key == "when":
                    role[key] = self._process_jinja_value(templar, value, implicit=True)
                else:
                    role[key] = self._process_jinja_value(templar, value)

    def _process_jinja_in_tasks_block(
        self, templar: Templar, ruamel_data: CommentedSeq
    ) -> None:
        task: CommentedMap
        for task in ruamel_data:
            for key, value in task.items():
                if key in NESTED_TASK_KEYS:
                    self._process_jinja_in_tasks_block(templar, value)
                elif key == "vars":
                    self._process_jinja_in_vars_block(templar, value)
                elif key.endswith("when"):
                    task[key] = self._process_jinja_value(templar, value, implicit=True)
                else:
                    task[key] = self._process_jinja_value(templar, value)

    def _process_jinja_in_vars_block(
        self, templar: Templar, ruamel_data: CommentedMap
    ) -> None:
        for key, value in ruamel_data.items():
            ruamel_data[key] = self._process_jinja_value(templar, value)

    def _process_jinja_in_inventory(
        self, templar: Templar, ruamel_data: CommentedMap | dict
    ) -> None:
        for key, value in ruamel_data.items():
            if key == "vars":
                self._process_jinja_in_vars_block(templar, value)
            elif isinstance(value, dict):
                self._process_jinja_in_inventory(templar, value)

    def _process_jinja_value(
        self, templar: Templar, value: Any, implicit: bool = False
    ) -> Any:
        if templar.is_possibly_template(value):
            return JinjaTemplate(
                value, implicit=implicit, jinja_env=templar.environment
            )
        elif isinstance(value, dict):
            for key, inner_value in value.items():
                value[key] = self._process_jinja_value(
                    templar, inner_value, implicit=implicit
                )
        elif isinstance(value, list):
            for index, item in enumerate(value):
                value[index] = self._process_jinja_value(
                    templar, item, implicit=implicit
                )
        return value
