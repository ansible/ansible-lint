# cspell:ignore classinfo
"""Transformer implementation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.yaml_utils import FormattedYAML, get_path_to_play, get_path_to_task

if TYPE_CHECKING:
    from ansiblelint.config import Options
    from ansiblelint.errors import MatchError
    from ansiblelint.runner import LintResult

__all__ = ["Transformer"]

_logger = logging.getLogger(__name__)


class Transformer:
    """Transformer class marshals transformations.

    The Transformer is similar to the ``ansiblelint.runner.Runner`` which manages
    running each of the rules. We only expect there to be one ``Transformer`` instance
    which should be instantiated from the main entrypoint function.

    In the future, the transformer will be responsible for running transforms for each
    of the rule matches. For now, it just reads/writes YAML files which is a
    pre-requisite for the planned rule-specific transforms.
    """

    DUMP_MSG = "Rewriting yaml file:"
    FIX_NA_MSG = "Rule specific fix not available for:"
    FIX_NE_MSG = "Rule specific fix not enabled for:"
    FIX_APPLY_MSG = "Applying rule specific fix for:"
    FIX_FAILED_MSG = "Rule specific fix failed for:"
    FIX_ISSUE_MSG = (
        "Please file an issue for this with the task or playbook that caused the error."
    )
    FIX_APPLIED_MSG = "Rule specific fix applied for:"
    FIX_NOT_APPLIED_MSG = "Rule specific fix not applied for:"

    def __init__(self, result: LintResult, options: Options):
        """Initialize a Transformer instance."""
        self.write_set = self.effective_write_set(options.write_list)

        self.matches: list[MatchError] = result.matches
        self.files: set[Lintable] = result.files

        lintables: dict[str, Lintable] = {file.filename: file for file in result.files}
        self.matches_per_file: dict[Lintable, list[MatchError]] = {
            file: [] for file in result.files
        }
        not_ignored = [match for match in self.matches if not match.ignored]
        for match in not_ignored:
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
                yaml = FormattedYAML(
                    # Ansible only uses YAML 1.1, but others files should use newer 1.2 (ruamel.yaml defaults to 1.2)
                    version=(1, 1) if file.is_owned_by_ansible() else None,
                )

                ruamel_data = yaml.load(data)
                if not isinstance(ruamel_data, CommentedMap | CommentedSeq):
                    # This is an empty vars file or similar which loads as None.
                    # It is not safe to write this file or data-loss is likely.
                    # Only maps and sequences can preserve comments. Skip it.
                    _logger.debug(
                        "Ignored reformatting %s because current implementation in ruamel.yaml would drop comments. See https://sourceforge.net/p/ruamel-yaml/tickets/460/",
                        file,
                    )
                    continue

            if self.write_set != {"none"}:
                self._do_transforms(file, ruamel_data or data, file_is_yaml, matches)

            if file_is_yaml:
                _logger.debug("%s %s, version=%s", self.DUMP_MSG, file, yaml.version)
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
            match_id = f"{match.tag}/{match.match_type} {match.filename}:{match.lineno}"
            if not isinstance(match.rule, TransformMixin):
                logging.debug("%s %s", self.FIX_NA_MSG, match_id)
                continue
            if self.write_set != {"all"}:
                rule = cast(AnsibleLintRule, match.rule)
                rule_definition = set(rule.tags)
                rule_definition.add(rule.id)
                if rule_definition.isdisjoint(self.write_set):
                    logging.debug("%s %s", self.FIX_NE_MSG, match_id)
                    continue
            if file_is_yaml and not match.yaml_path:
                data = cast(CommentedMap | CommentedSeq, data)
                if match.match_type == "play":
                    match.yaml_path = get_path_to_play(file, match.lineno, data)
                elif match.task or file.kind in (
                    "tasks",
                    "handlers",
                    "playbook",
                ):
                    match.yaml_path = get_path_to_task(file, match.lineno, data)

            logging.debug("%s %s", self.FIX_APPLY_MSG, match_id)
            try:
                match.rule.transform(match, file, data)
            except Exception as exc:  # pylint: disable=broad-except
                _logger.error("%s %s", self.FIX_FAILED_MSG, match_id)  # noqa: TRY400
                _logger.exception(exc)  # noqa: TRY401
                _logger.error(self.FIX_ISSUE_MSG)  # noqa: TRY400
                continue
            if match.fixed:
                _logger.debug("%s %s", self.FIX_APPLIED_MSG, match_id)
            else:
                _logger.error("%s %s", self.FIX_NOT_APPLIED_MSG, match_id)
