"""All internal ansible-lint rules."""
import copy
import glob
import importlib.util
import inspect
import logging
import os
import re
from argparse import Namespace
from collections import defaultdict
from functools import lru_cache
from importlib.abc import Loader
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Set,
    Union,
    cast,
)

from ruamel.yaml.comments import CommentedMap, CommentedSeq

import ansiblelint.skip_utils
import ansiblelint.utils
import ansiblelint.yaml_utils
from ansiblelint._internal.rules import (
    AnsibleParserErrorRule,
    BaseRule,
    LoadingFailureRule,
    RuntimeErrorRule,
)
from ansiblelint.config import get_rule_config
from ansiblelint.config import options as default_options
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
    def rule_config(self) -> Dict[str, Any]:
        """Retrieve rule specific configuration."""
        return get_rule_config(self.id)

    @lru_cache(maxsize=256)
    def get_config(self, key: str) -> Any:
        """Return a configured value for given key string."""
        return self.rule_config.get(key, None)

    def __repr__(self) -> str:
        """Return a AnsibleLintRule instance representation."""
        return self.id + ": " + self.shortdesc

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
        message: Optional[str] = None,
        linenumber: int = 1,
        details: str = "",
        filename: Optional[Union[str, Lintable]] = None,
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
        match_type: Optional[str] = None
        while not match_type and frame is not None:
            func_name = frame.f_code.co_name
            match_type = match_types.get(func_name, None)
            if match_type:
                # add the match_type to the match
                match.match_type = match_type
                break
            frame = frame.f_back  # get the parent frame for the next iteration
        return match

    def matchlines(self, file: "Lintable") -> List[MatchError]:
        matches: List[MatchError] = []
        if not self.match:
            return matches
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

    def matchtasks(self, file: Lintable) -> List[MatchError]:
        matches: List[MatchError] = []
        if (
            not self.matchtask
            or file.kind not in ["handlers", "tasks", "playbook"]
            or str(file.base_kind) != "text/yaml"
        ):
            return matches

        tasks_iterator = ansiblelint.yaml_utils.iter_tasks_in_file(file, self.id)
        for raw_task, task, skipped, error in tasks_iterator:
            if error is not None:
                # normalize_task converts AnsibleParserError to MatchError
                return [error]

            if skipped or "action" not in task:
                continue

            if self.needs_raw_task:
                task["__raw_task__"] = raw_task

            result = self.matchtask(task, file=file)

            if not result:
                continue

            message = None
            if isinstance(result, str):
                message = result
            task_msg = "Task/Handler: " + ansiblelint.utils.task_to_str(task)
            match = self.create_matcherror(
                message=message,
                linenumber=task[ansiblelint.utils.LINE_NUMBER_KEY],
                details=task_msg,
                filename=file,
            )
            match.task = task
            matches.append(match)
        return matches

    def matchyaml(self, file: Lintable) -> List[MatchError]:
        matches: List[MatchError] = []
        if not self.matchplay or str(file.base_kind) != "text/yaml":
            return matches

        yaml = ansiblelint.utils.parse_yaml_linenumbers(file)
        # yaml returned can be an AnsibleUnicode (a string) when the yaml
        # file contains a single string. YAML spec allows this but we consider
        # this an fatal error.
        if isinstance(yaml, str):
            if yaml.startswith("$ANSIBLE_VAULT"):
                return []
            return [MatchError(filename=str(file.path), rule=LoadingFailureRule())]
        if not yaml:
            return matches

        if isinstance(yaml, dict):
            yaml = [yaml]

        yaml = ansiblelint.skip_utils.append_skipped_rules(yaml, file)

        for play in yaml:

            # Bug #849
            if play is None:
                continue

            if self.id in play.get("skipped_rules", ()):
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
        data: Union[CommentedMap, CommentedSeq, str],
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
        yaml_path: List[Union[int, str]],
        data: Union[MutableMapping[str, Any], MutableSequence[Any], str],
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


def is_valid_rule(rule: Any) -> bool:
    """Check if given rule is valid or not."""
    return issubclass(rule, AnsibleLintRule) and bool(rule.id) and bool(rule.shortdesc)


# pylint: disable=too-many-nested-blocks
def load_plugins(directory: str) -> Iterator[AnsibleLintRule]:
    """Yield a rule class."""
    for pluginfile in glob.glob(os.path.join(directory, "[A-Za-z]*.py")):

        pluginname = os.path.basename(pluginfile.replace(".py", ""))
        spec = importlib.util.spec_from_file_location(pluginname, pluginfile)

        # https://github.com/python/typeshed/issues/2793
        if spec and isinstance(spec.loader, Loader):

            # load rule markdown documentation if found
            help_md = ""
            if spec.origin:
                md_filename = os.path.splitext(spec.origin)[0] + ".md"
                if os.path.exists(md_filename):
                    with open(md_filename, encoding="utf-8") as f:
                        help_md = f.read()

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                for _, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and is_valid_rule(obj):
                        if help_md:
                            obj.help = help_md
                        yield obj()

            except (TypeError, ValueError, AttributeError) as exc:
                _logger.warning(
                    "Skipped invalid rule from %s due to %s", pluginname, exc
                )


class RulesCollection:
    """Container for a collection of rules."""

    def __init__(
        self,
        rulesdirs: Optional[List[str]] = None,
        options: Namespace = default_options,
    ) -> None:
        """Initialize a RulesCollection instance."""
        self.options = options
        if rulesdirs is None:
            rulesdirs = []
        self.rulesdirs = expand_paths_vars(rulesdirs)
        self.rules: List[BaseRule] = []
        # internal rules included in order to expose them for docs as they are
        # not directly loaded by our rule loader.
        self.rules.extend(
            [RuntimeErrorRule(), AnsibleParserErrorRule(), LoadingFailureRule()]
        )
        for rulesdir in self.rulesdirs:
            _logger.debug("Loading rules from %s", rulesdir)
            for rule in load_plugins(rulesdir):
                self.register(rule)
        self.rules = sorted(self.rules)

    def register(self, obj: AnsibleLintRule) -> None:
        """Register a rule."""
        # We skip opt-in rules which were not manually enabled.
        # But we do include opt-in rules when listing all rules or tags
        if any(
            [
                "opt-in" not in obj.tags,
                obj.id in self.options.enable_list,
                self.options.listrules,
                self.options.listtags,
            ]
        ):
            self.rules.append(obj)

    def __iter__(self) -> Iterator[BaseRule]:
        """Return the iterator over the rules in the RulesCollection."""
        return iter(self.rules)

    def __len__(self) -> int:
        """Return the length of the RulesCollection data."""
        return len(self.rules)

    def extend(self, more: List[AnsibleLintRule]) -> None:
        """Combine rules."""
        self.rules.extend(more)

    def run(
        self,
        file: Lintable,
        tags: Optional[Set[str]] = None,
        skip_list: Optional[List[str]] = None,
    ) -> List[MatchError]:
        """Run all the rules against the given lintable."""
        matches: List[MatchError] = []
        if tags is None:
            tags = set()
        if skip_list is None:
            skip_list = []

        if not file.path.is_dir():
            try:
                if file.content is not None:  # loads the file content
                    pass
            except (IOError, UnicodeDecodeError) as exc:
                return [
                    MatchError(
                        message=str(exc),
                        filename=file,
                        rule=LoadingFailureRule(),
                        tag=f"{LoadingFailureRule.id}[{exc.__class__.__name__.lower()}]",
                    )
                ]

        for rule in self.rules:
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

    def listtags(self) -> str:
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
