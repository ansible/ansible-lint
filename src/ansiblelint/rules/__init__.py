"""All internal ansible-lint rules."""
import copy
import glob
import importlib.util
import logging
import os
import re
from argparse import Namespace
from collections import defaultdict
from functools import lru_cache
from importlib.abc import Loader
from typing import Any, Dict, Iterator, List, Optional, Set, Union

import ansiblelint.utils
from ansiblelint._internal.rules import (
    AnsibleParserErrorRule,
    BaseRule,
    LoadingFailureRule,
    RuntimeErrorRule,
)
from ansiblelint.config import get_rule_config, options
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.skip_utils import append_skipped_rules, get_rule_skips_from_line

_logger = logging.getLogger(__name__)


class AnsibleLintRule(BaseRule):
    @property
    def rule_config(self) -> Dict[str, Any]:
        return get_rule_config(self.id)

    @lru_cache()
    def get_config(self, key: str) -> Any:
        """Return a configured value for given key string."""
        return self.rule_config.get(key, None)

    def __repr__(self) -> str:
        """Return a AnsibleLintRule instance representation."""
        return self.id + ": " + self.shortdesc

    @staticmethod
    def unjinja(text: str) -> str:
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
        match = MatchError(
            message=message,
            linenumber=linenumber,
            details=details,
            filename=filename,
            rule=copy.copy(self),
        )
        if tag:
            match.tag = tag
        return match

    def matchlines(self, file: "Lintable") -> List[MatchError]:
        matches: List[MatchError] = []
        if not self.match:
            return matches
        # arrays are 0-based, line numbers are 1-based
        # so use prev_line_no as the counter
        for (prev_line_no, line) in enumerate(file.content.split("\n")):
            if line.lstrip().startswith('#'):
                continue

            rule_id_list = get_rule_skips_from_line(line)
            if self.id in rule_id_list:
                continue

            result = self.match(line)
            if not result:
                continue
            message = None
            if isinstance(result, str):
                message = result
            m = self.create_matcherror(
                message=message,
                linenumber=prev_line_no + 1,
                details=line,
                filename=file,
            )
            matches.append(m)
        return matches

    # TODO(ssbarnea): Reduce mccabe complexity
    # https://github.com/ansible-community/ansible-lint/issues/744
    def matchtasks(self, file: Lintable) -> List[MatchError]:
        matches: List[MatchError] = []
        if (
            not self.matchtask
            or file.kind not in ['handlers', 'tasks', 'playbook']
            or str(file.base_kind) != 'text/yaml'
        ):
            return matches

        yaml = ansiblelint.utils.parse_yaml_linenumbers(file)
        if not yaml:
            return matches

        yaml = append_skipped_rules(yaml, file)

        try:
            tasks = ansiblelint.utils.get_normalized_tasks(yaml, file)
        except MatchError as e:
            return [e]

        for task in tasks:
            if self.id in task.get('skipped_rules', ()):
                continue

            if 'action' not in task:
                continue
            result = self.matchtask(task, file=file)
            if not result:
                continue

            message = None
            if isinstance(result, str):
                message = result
            task_msg = "Task/Handler: " + ansiblelint.utils.task_to_str(task)
            m = self.create_matcherror(
                message=message,
                linenumber=task[ansiblelint.utils.LINE_NUMBER_KEY],
                details=task_msg,
                filename=file,
            )
            matches.append(m)
        return matches

    def matchyaml(self, file: Lintable) -> List[MatchError]:
        matches: List[MatchError] = []
        if not self.matchplay or str(file.base_kind) != 'text/yaml':
            return matches

        yaml = ansiblelint.utils.parse_yaml_linenumbers(file)
        # yaml returned can be an AnsibleUnicode (a string) when the yaml
        # file contains a single string. YAML spec allows this but we consider
        # this an fatal error.
        if isinstance(yaml, str):
            if yaml.startswith('$ANSIBLE_VAULT'):
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

            if self.id in play.get('skipped_rules', ()):
                continue

            matches.extend(self.matchplay(file, play))

        return matches


def is_valid_rule(rule: AnsibleLintRule) -> bool:
    """Check if given rule is valid or not."""
    return isinstance(rule, AnsibleLintRule) and bool(rule.id) and bool(rule.shortdesc)


def load_plugins(directory: str) -> Iterator[AnsibleLintRule]:
    """Yield a rule class."""
    for pluginfile in glob.glob(os.path.join(directory, '[A-Za-z]*.py')):

        pluginname = os.path.basename(pluginfile.replace('.py', ''))
        spec = importlib.util.spec_from_file_location(pluginname, pluginfile)
        # https://github.com/python/typeshed/issues/2793
        if spec and isinstance(spec.loader, Loader):
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                rule = getattr(module, pluginname)()
                if is_valid_rule(rule):
                    yield rule

            except (TypeError, ValueError, AttributeError):
                _logger.warning("Skipped invalid rule from %s", pluginname)


class RulesCollection:
    def __init__(
        self, rulesdirs: Optional[List[str]] = None, options: Namespace = options
    ) -> None:
        """Initialize a RulesCollection instance."""
        self.options = options
        if rulesdirs is None:
            rulesdirs = []
        self.rulesdirs = ansiblelint.file_utils.expand_paths_vars(rulesdirs)
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
        # We skip opt-in rules which were not manually enabled
        if 'opt-in' not in obj.tags or obj.id in self.options.enable_list:
            self.rules.append(obj)

    def __iter__(self) -> Iterator[BaseRule]:
        """Return the iterator over the rules in the RulesCollection."""
        return iter(self.rules)

    def __len__(self) -> int:
        """Return the length of the RulesCollection data."""
        return len(self.rules)

    def extend(self, more: List[AnsibleLintRule]) -> None:
        self.rules.extend(more)

    def run(
        self, file: Lintable, tags: Set[str] = set(), skip_list: List[str] = []
    ) -> List[MatchError]:
        matches: List[MatchError] = list()

        if not file.path.is_dir():
            try:
                if file.content is not None:  # loads the file content
                    pass
            except IOError as e:
                return [
                    MatchError(
                        message=str(e),
                        filename=file,
                        rule=LoadingFailureRule(),
                        tag=e.__class__.__name__.lower(),
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
        tag_desc = {
            "behaviour": "Indicates a bad practice or behavior",
            "command-shell": "Specific to use of command and shell modules",
            "core": "Related to internal implementation of the linter",
            "deprecations": "Indicate use of features that are removed from Ansible",
            "experimental": "Newly introduced rules, by default triggering only warnings",
            "formatting": "Related to code-style",
            "idempotency": "Possible indication that consequent runs would produce different results",
            "idiom": "Anti-pattern detected, likely to cause undesired behavior",
            "metadata": "Invalid metadata, likely related to galaxy, collections or roles",
            "yaml": "External linter which will also produce its own rule codes.",
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
