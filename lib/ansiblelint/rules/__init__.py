"""All internal ansible-lint rules."""
import re
from collections import defaultdict
import glob
import importlib.util
import logging
import os
from typing import List

from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.skip_utils import append_skipped_rules
from ansiblelint.errors import Match
import ansiblelint.utils


_logger = logging.getLogger(__name__)


def load_plugins(directory):
    """Return a list of rule classes."""
    result = []

    for pluginfile in glob.glob(os.path.join(directory, '[A-Za-z]*.py')):

        pluginname = os.path.basename(pluginfile.replace('.py', ''))
        spec = importlib.util.spec_from_file_location(pluginname, pluginfile)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        obj = getattr(module, pluginname)()
        result.append(obj)
    return result


class AnsibleLintRule(object):

    def __repr__(self):
        """Return a AnsibleLintRule instance representation."""
        return self.id + ": " + self.shortdesc

    def verbose(self):
        return self.id + ": " + self.shortdesc + "\n  " + self.description

    match = None
    matchtask = None
    matchplay = None

    @staticmethod
    def unjinja(text):
        return re.sub(r"{{[^}]*}}", "JINJA_VAR", text)

    def matchlines(self, file, text):
        matches = []
        if not self.match:
            return matches
        # arrays are 0-based, line numbers are 1-based
        # so use prev_line_no as the counter
        for (prev_line_no, line) in enumerate(text.split("\n")):
            if line.lstrip().startswith('#'):
                continue

            rule_id_list = get_rule_skips_from_line(line)
            if self.id in rule_id_list:
                continue

            result = self.match(file, line)
            if not result:
                continue
            message = None
            if isinstance(result, str):
                message = result
            matches.append(Match(prev_line_no + 1, line,
                           file['path'], self, message))
        return matches

    def matchtasks(self, file, text):
        matches = []
        if not self.matchtask:
            return matches

        if file['type'] == 'meta':
            return matches

        yaml = ansiblelint.utils.parse_yaml_linenumbers(text, file['path'])
        if not yaml:
            return matches

        yaml = append_skipped_rules(yaml, text, file['type'])

        for task in ansiblelint.utils.get_normalized_tasks(yaml, file):
            if self.id in task.get('skipped_rules', ()):
                continue

            if 'action' not in task:
                continue
            result = self.matchtask(file, task)
            if not result:
                continue

            message = None
            if isinstance(result, str):
                message = result
            task_msg = "Task/Handler: " + ansiblelint.utils.task_to_str(task)
            matches.append(Match(task[ansiblelint.utils.LINE_NUMBER_KEY], task_msg,
                           file['path'], self, message))
        return matches

    @staticmethod
    def _matchplay_linenumber(play, optional_linenumber):
        try:
            linenumber, = optional_linenumber
        except ValueError:
            linenumber = play[ansiblelint.utils.LINE_NUMBER_KEY]
        return linenumber

    def matchyaml(self, file, text):
        matches = []
        if not self.matchplay:
            return matches

        yaml = ansiblelint.utils.parse_yaml_linenumbers(text, file['path'])
        if not yaml:
            return matches

        if isinstance(yaml, dict):
            yaml = [yaml]

        yaml = ansiblelint.skip_utils.append_skipped_rules(yaml, text, file['type'])

        for play in yaml:
            if self.id in play.get('skipped_rules', ()):
                continue

            result = self.matchplay(file, play)
            if not result:
                continue

            if isinstance(result, tuple):
                result = [result]

            if not isinstance(result, list):
                raise TypeError("{} is not a list".format(result))

            for section, message, *optional_linenumber in result:
                linenumber = self._matchplay_linenumber(play, optional_linenumber)
                matches.append(Match(linenumber,
                                     section, file['path'], self, message))
        return matches


class RulesCollection(object):

    def __init__(self, rulesdirs=None):
        """Initialize a RulesCollection instance."""
        if rulesdirs is None:
            rulesdirs = []
        self.rulesdirs = ansiblelint.utils.expand_paths_vars(rulesdirs)
        self.rules = []
        for rulesdir in self.rulesdirs:
            _logger.debug("Loading rules from %s", rulesdir)
            self.extend(load_plugins(rulesdir))
        self.rules = sorted(self.rules, key=lambda r: r.id)

    def register(self, obj):
        self.rules.append(obj)

    def __iter__(self):
        """Return the iterator over the rules in the RulesCollection."""
        return iter(self.rules)

    def __len__(self):
        """Return the length of the RulesCollection data."""
        return len(self.rules)

    def extend(self, more):
        self.rules.extend(more)

    def run(self, playbookfile, tags=set(), skip_list=frozenset()) -> List:
        text = ""
        matches: List = list()

        try:
            with open(playbookfile['path'], mode='r', encoding='utf-8') as f:
                text = f.read()
        except IOError as e:
            _logger.warning(
                "Couldn't open %s - %s",
                playbookfile['path'],
                e.strerror)
            return matches

        for rule in self.rules:
            if not tags or not set(rule.tags).union([rule.id]).isdisjoint(tags):
                rule_definition = set(rule.tags)
                rule_definition.add(rule.id)
                if set(rule_definition).isdisjoint(skip_list):
                    matches.extend(rule.matchlines(playbookfile, text))
                    matches.extend(rule.matchtasks(playbookfile, text))
                    matches.extend(rule.matchyaml(playbookfile, text))

        return matches

    def __repr__(self):
        """Return a RulesCollection instance representation."""
        return "\n".join([rule.verbose()
                          for rule in sorted(self.rules, key=lambda x: x.id)])

    def listtags(self):
        tags = defaultdict(list)
        for rule in self.rules:
            for tag in rule.tags:
                tags[tag].append("[{0}]".format(rule.id))
        results = []
        for tag in sorted(tags):
            results.append("{0} {1}".format(tag, tags[tag]))
        return "\n".join(results)
