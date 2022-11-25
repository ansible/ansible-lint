"""All internal ansible-lint rules."""
from __future__ import annotations

import copy
import inspect
import logging
import re
import sys
from argparse import Namespace
from collections import defaultdict
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any, Iterable, Iterator, MutableMapping, MutableSequence, cast

from ruamel.yaml.comments import CommentedMap, CommentedSeq

import ansiblelint.skip_utils
import ansiblelint.utils
import ansiblelint.yaml_utils
from ansiblelint._internal.rules import (
    AnsibleParserErrorRule,
    BaseRule,
    LoadingFailureRule,
    RuntimeErrorRule,
    WarningRule,
)
from ansiblelint.config import PROFILES, get_rule_config
from ansiblelint.config import options as default_options
from ansiblelint.constants import LINE_NUMBER_KEY, RULE_DOC_URL, SKIPPED_RULES_KEY
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable, expand_paths_vars

_logger = logging.getLogger(__name__)

match_types = {
    "matchlines": "line",
    "match": "line",  # called by matchlines
    "matchtasks": "task",
    "matchtask": "task",  # called by matchtasks
    "matchyaml": "yaml",
    "matchplay": "play",  # called by matchyaml
    "matchdir": "dir",
}


class AnsibleLintRule(BaseRule):
    """AnsibleLintRule should be used as base for writing new rules."""

    @property
    def url(self) -> str:
        """Return rule documentation url."""
        return RULE_DOC_URL + self.id + "/"

    @property
    def rule_config(self) -> dict[str, Any]:
        """Retrieve rule specific configuration."""
        return get_rule_config(self.id)

    @lru_cache(maxsize=256)
    def get_config(self, key: str) -> Any:
        """Return a configured value for given key string."""
        return self.rule_config.get(key, None)

    @staticmethod
    def unjinja(text: str) -> str:
        """Remove jinja2 bits from a string."""
        text = re.sub(r"{{.+?}}", "JINJA_EXPRESSION", text)
        text = re.sub(r"{%.+?%}", "JINJA_STATEMENT", text)
        text = re.sub(r"{#.+?#}", "JINJA_COMMENT", text)
        return text

    # pylint: disable=too-many-arguments
    def create_matcherror(
        self,
        message: str | None = None,
        linenumber: int = 1,
        details: str = "",
        filename: Lintable | None = None,
        tag: str = "",
    ) -> MatchError:
        """Instantiate a new MatchError."""
        match = MatchError(
            message=message,
            linenumber=linenumber,
            details=details,
            filename=filename,
            rule=copy.copy(self),
        )
        if tag:
            match.tag = tag
        # search through callers to find one of the match* methods
        frame = inspect.currentframe()
        match_type: str | None = None
        while not match_type and frame is not None:
            func_name = frame.f_code.co_name
            match_type = match_types.get(func_name, None)
            if match_type:
                # add the match_type to the match
                match.match_type = match_type
                break
            frame = frame.f_back  # get the parent frame for the next iteration
        return match

    @staticmethod
    def _enrich_matcherror_with_task_details(
        match: MatchError, task: dict[str, Any]
    ) -> None:
        match.task = task
        if not match.details:
            match.details = "Task/Handler: " + ansiblelint.utils.task_to_str(task)
        if match.linenumber < task[LINE_NUMBER_KEY]:
            match.linenumber = task[LINE_NUMBER_KEY]

    def matchlines(self, file: Lintable) -> list[MatchError]:
        matches: list[MatchError] = []
        # arrays are 0-based, line numbers are 1-based
        # so use prev_line_no as the counter
        for (prev_line_no, line) in enumerate(file.content.split("\n")):
            if line.lstrip().startswith("#"):
                continue

            rule_id_list = ansiblelint.skip_utils.get_rule_skips_from_line(line)
            if self.id in rule_id_list:
                continue

            result = self.match(line)
            if not result:
                continue
            message = None
            if isinstance(result, str):
                message = result
            matcherror = self.create_matcherror(
                message=message,
                linenumber=prev_line_no + 1,
                details=line,
                filename=file,
            )
            matches.append(matcherror)
        return matches

    # pylint: disable=too-many-branches
    def matchtasks(self, file: Lintable) -> list[MatchError]:  # noqa: C901
        """Call matchtask for each task inside file and return aggregate results.

        Most rules will never need to override matchtasks because its main
        purpose is to call matchtask for each task/handlers in the same file,
        and to aggregate the results.
        """
        matches: list[MatchError] = []
        if (
            file.kind not in ["handlers", "tasks", "playbook"]
            or str(file.base_kind) != "text/yaml"
        ):
            return matches

        tasks_iterator = ansiblelint.yaml_utils.iter_tasks_in_file(file)
        for raw_task, task, skipped_tags, error in tasks_iterator:
            if error is not None:
                # normalize_task converts AnsibleParserError to MatchError
                return [error]

            if (
                self.id in skipped_tags
                or ("action" not in task)
                or "skip_ansible_lint" in task.get("tags", [])
            ):
                continue

            if self.needs_raw_task:
                task["__raw_task__"] = raw_task

            result = self.matchtask(task, file=file)
            if not result:
                continue

            if isinstance(result, Iterable) and not isinstance(
                result, str
            ):  # list[MatchError]
                # https://github.com/PyCQA/pylint/issues/6044
                # pylint: disable=not-an-iterable
                for match in result:
                    if match.tag in skipped_tags:
                        continue
                    self._enrich_matcherror_with_task_details(match, task)
                    matches.append(match)
                continue
            if isinstance(result, MatchError):
                if result.tag in skipped_tags:
                    continue
                match = result
            else:  # bool or string
                message = None
                if isinstance(result, str):
                    message = result
                match = self.create_matcherror(
                    message=message,
                    linenumber=task[LINE_NUMBER_KEY],
                    filename=file,
                )

            self._enrich_matcherror_with_task_details(match, task)
            matches.append(match)
        return matches

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        matches: list[MatchError] = []
        if str(file.base_kind) != "text/yaml":
            return matches

        yaml = file.data
        # yaml returned can be an AnsibleUnicode (a string) when the yaml
        # file contains a single string. YAML spec allows this but we consider
        # this an fatal error.
        if isinstance(yaml, str):
            if yaml.startswith("$ANSIBLE_VAULT"):
                return []
            return [MatchError(filename=file, rule=LoadingFailureRule())]
        if not yaml:
            return matches

        if isinstance(yaml, dict):
            yaml = [yaml]

        for play in yaml:

            # Bug #849
            if play is None:
                continue

            if self.id in play.get(SKIPPED_RULES_KEY, ()):
                continue

            if "skip_ansible_lint" in play.get("tags", []):
                continue

            matches.extend(self.matchplay(file, play))

        return matches


class TransformMixin:
    """A mixin for AnsibleLintRule to enable transforming files.

    If ansible-lint is started with the ``--write`` option, then the ``Transformer``
    will call the ``transform()`` method for every MatchError identified if the rule
    that identified it subclasses this ``TransformMixin``. Only the rule that identified
    a MatchError can do transforms to fix that match.
    """

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: CommentedMap | CommentedSeq | str,
    ) -> None:
        """Transform ``data`` to try to fix the MatchError identified by this rule.

        The ``match`` was generated by this rule in the ``lintable`` file.
        When ``transform()`` is called on a rule, the rule should either fix the
        issue, if possible, or make modifications that make it easier to fix manually.

        The transform must set ``match.fixed = True`` when data has been transformed to
        fix the error.

        For YAML files, ``data`` is an editable YAML dict/array that preserves
        any comments that were in the original file.

        .. code:: python

            data[0]["tasks"][0]["when"] = False

        This is easier with the ``seek()`` utility method:

        .. code :: python

            target_task = self.seek(match.yaml_path, data)
            target_task["when"] = False

        For any files that aren't YAML, ``data`` is the loaded file's content as a string.
        To edit non-YAML files, save the updated contents in ``lintable.content``:

        .. code:: python

            new_data = self.do_something_to_fix_the_match(data)
            lintable.content = new_data
        """

    @staticmethod
    def seek(
        yaml_path: list[int | str],
        data: MutableMapping[str, Any] | MutableSequence[Any] | str,
    ) -> Any:
        """Get the element identified by ``yaml_path`` in ``data``.

        Rules that work with YAML need to seek, or descend, into nested YAML data
        structures to perform the relevant transforms. For example:

        .. code:: python

            def transform(self, match, lintable, data):
                target_task = self.seek(match.yaml_path, data)
                # transform target_task
        """
        if isinstance(data, str):
            # can't descend into a string
            return data
        target = data
        for segment in yaml_path:
            # The cast() calls tell mypy what types we expect.
            # Essentially this does:
            #   target = target[segment]
            if isinstance(segment, str):
                target = cast(MutableMapping[str, Any], target)[segment]
            elif isinstance(segment, int):
                target = cast(MutableSequence[Any], target)[segment]
        return target


# pylint: disable=too-many-nested-blocks
def load_plugins(  # noqa: max-complexity: 11
    dirs: list[str],
) -> Iterator[AnsibleLintRule]:
    """Yield a rule class."""

    def all_subclasses(cls: type) -> set[type]:
        return set(cls.__subclasses__()).union(
            [s for c in cls.__subclasses__() for s in all_subclasses(c)]
        )

    orig_sys_path = sys.path.copy()

    for directory in dirs:
        if directory not in sys.path:
            sys.path.append(str(directory))

        # load all modules in the directory
        for f in Path(directory).glob("*.py"):
            if "__" not in f.stem and f.stem not in "conftest":
                try:
                    import_module(f"{f.stem}")

                except ImportError as exc:
                    _logger.warning("Ignore loading rule from %s due to %s", f, exc)
    # restore sys.path
    sys.path = orig_sys_path

    rules: dict[str, BaseRule] = {}
    for rule in all_subclasses(BaseRule):
        # we do not return the rules that are not loaded from passed 'directory'
        # or rules that do not have a valid id. For example, during testing
        # python may load other rule classes, some outside the tested rule
        # directories.
        if getattr(rule, "id") and Path(inspect.getfile(rule)).parent.absolute() in [
            Path(x).absolute() for x in dirs
        ]:
            if issubclass(rule, BaseRule) and rule.id not in rules:
                rules[rule.id] = rule()
    for rule in rules.values():  # type: ignore
        if isinstance(rule, AnsibleLintRule) and bool(rule.id):
            yield rule


class RulesCollection:
    """Container for a collection of rules."""

    def __init__(
        self,
        rulesdirs: list[str] | None = None,
        options: Namespace = default_options,
        profile_name: str | None = None,
        conditional: bool = True,
    ) -> None:
        """Initialize a RulesCollection instance."""
        self.options = options
        self.profile = []
        if profile_name:
            self.profile = PROFILES[profile_name]
        if rulesdirs is None:
            rulesdirs = []
        self.rulesdirs = expand_paths_vars(rulesdirs)
        self.rules: list[BaseRule] = []
        # internal rules included in order to expose them for docs as they are
        # not directly loaded by our rule loader.
        self.rules.extend(
            [
                RuntimeErrorRule(),
                AnsibleParserErrorRule(),
                LoadingFailureRule(),
                WarningRule(),
            ]
        )
        for rule in load_plugins(rulesdirs):
            self.register(rule, conditional=conditional)
        self.rules = sorted(self.rules)

        # when we have a profile we unload some of the rules
        if profile_name:
            filter_rules_with_profile(self.rules, profile_name)

    def register(self, obj: AnsibleLintRule, conditional: bool = False) -> None:
        """Register a rule."""
        # We skip opt-in rules which were not manually enabled.
        # But we do include opt-in rules when listing all rules or tags
        if any(
            [
                not conditional,
                self.profile,  # when profile is used we load all rules and filter later
                "opt-in" not in obj.tags,
                obj.id in self.options.enable_list,
                self.options.list_rules,
                self.options.list_tags,
            ]
        ):
            obj._collection = self  # pylint: disable=protected-access
            self.rules.append(obj)

    def __iter__(self) -> Iterator[BaseRule]:
        """Return the iterator over the rules in the RulesCollection."""
        return iter(sorted(self.rules))

    def alphabetical(self) -> Iterator[BaseRule]:
        """Return an iterator over the rules in the RulesCollection in alphabetical order."""
        return iter(sorted(self.rules, key=lambda x: x.id))

    def __len__(self) -> int:
        """Return the length of the RulesCollection data."""
        return len(self.rules)

    def extend(self, more: list[AnsibleLintRule]) -> None:
        """Combine rules."""
        self.rules.extend(more)

    def run(  # noqa: max-complexity: 12
        self,
        file: Lintable,
        tags: set[str] | None = None,
        skip_list: list[str] | None = None,
    ) -> list[MatchError]:
        """Run all the rules against the given lintable."""
        matches: list[MatchError] = []
        if tags is None:
            tags = set()
        if skip_list is None:
            skip_list = []

        if not file.path.is_dir():
            try:
                if file.content is not None:  # loads the file content
                    pass
            except (OSError, UnicodeDecodeError) as exc:
                return [
                    MatchError(
                        message=str(exc),
                        filename=file,
                        rule=LoadingFailureRule(),
                        tag=f"{LoadingFailureRule.id}[{exc.__class__.__name__.lower()}]",
                    )
                ]

        for rule in self.rules:
            if rule.id == "syntax-check":
                continue
            if (
                not tags
                or rule.has_dynamic_tags
                or not set(rule.tags).union([rule.id]).isdisjoint(tags)
            ):
                rule_definition = set(rule.tags)
                rule_definition.add(rule.id)
                if set(rule_definition).isdisjoint(skip_list):
                    matches.extend(rule.getmatches(file))

        # some rules can produce matches with tags that are inside our
        # skip_list, so we need to cleanse the matches
        matches = [m for m in matches if m.tag not in skip_list]

        return matches

    def __repr__(self) -> str:
        """Return a RulesCollection instance representation."""
        return "\n".join(
            [rule.verbose() for rule in sorted(self.rules, key=lambda x: x.id)]
        )

    def list_tags(self) -> str:
        """Return a string with all the tags in the RulesCollection."""
        tag_desc = {
            "command-shell": "Specific to use of command and shell modules",
            "core": "Related to internal implementation of the linter",
            "deprecations": "Indicate use of features that are removed from Ansible",
            "experimental": "Newly introduced rules, by default triggering only warnings",
            "formatting": "Related to code-style",
            "idempotency": "Possible indication that consequent runs would produce different results",
            "idiom": "Anti-pattern detected, likely to cause undesired behavior",
            "metadata": "Invalid metadata, likely related to galaxy, collections or roles",
            "opt-in": "Rules that are not used unless manually added to `enable_list`",
            "security": "Rules related o potentially security issues, like exposing credentials",
            "unpredictability": "Warn about code that might not work in a predictable way",
            "unskippable": "Indicate a fatal error that cannot be ignored or disabled",
            "yaml": "External linter which will also produce its own rule codes",
        }

        tags = defaultdict(list)
        for rule in self.rules:
            for tag in rule.tags:
                tags[tag].append(rule.id)
        result = "# List of tags and rules they cover\n"
        for tag in sorted(tags):
            desc = tag_desc.get(tag, None)
            if desc:
                result += f"{tag}:  # {desc}\n"
            else:
                result += f"{tag}:\n"
            # result += f"  rules:\n"
            for name in tags[tag]:
                result += f"  - {name}\n"
        return result


def filter_rules_with_profile(rule_col: list[BaseRule], profile: str) -> None:
    """Unload rules that are not part of the specified profile."""
    included = set()
    extends = profile
    total_rules = len(rule_col)
    while extends:
        for rule in PROFILES[extends]["rules"]:
            _logger.debug("Activating rule `%s` due to profile `%s`", rule, extends)
            included.add(rule)
        extends = PROFILES[extends].get("extends", None)
    for rule in rule_col.copy():
        if rule.id not in included:
            _logger.debug(
                "Unloading %s rule due to not being part of %s profile.",
                rule.id,
                profile,
            )
            rule_col.remove(rule)
        else:
            for tag in ("opt-in", "experimental"):
                if tag in rule.tags:
                    _logger.debug(
                        "Removing tag `%s` from `%s` rule because `%s` profile makes it mandatory.",
                        tag,
                        rule.id,
                        profile,
                    )
                    rule.tags.remove(tag)
                    # rule_col.rules.remove(rule)
                    # break
            if "opt-in" in rule.tags:
                rule.tags.remove("opt-in")
    _logger.debug("%s/%s rules included in the profile", len(rule_col), total_rules)
