# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from collections import defaultdict
import os

import ansiblelint.utils


class AnsibleLintRule(object):

    def __repr__(self):
        return self.id + ": " + self.shortdesc

    def verbose(self):
        return self.id + ": " + self.shortdesc + "\n  " + self.description

    def match(self, file="", line=""):
        return []

    def matchlines(self, file, text):
        matches = []
        # arrays are 0-based, line numbers are 1-based
        # so use prev_line_no as the counter
        for (prev_line_no, line) in enumerate(text.split("\n")):
            result = self.match(file, line)
            if result:
                message = None
                if isinstance(result, str):
                    message = result
                matches.append(Match(prev_line_no+1, line,
                               file['path'], self, message))
        return matches

    def matchtask(self, file="", task=None):
        return []

    def matchtasks(self, file, text):
        matches = []
        yaml = ansiblelint.utils.parse_yaml_linenumbers(text)
        if yaml:
            for task in ansiblelint.utils.get_action_tasks(yaml, file):
                if 'skip_ansible_lint' in task.get('tags', []):
                    continue
                if 'action' in task:
                    result = self.matchtask(file, task)
                    if result:
                        message = None
                        if isinstance(result, str):
                            message = result
                        taskstr = "Task/Handler: " + ansiblelint.utils.task_to_str(task)
                        matches.append(Match(task[ansiblelint.utils.LINE_NUMBER_KEY], taskstr,
                                       file['path'], self, message))
        return matches

    def matchyaml(self, file, text):
        matches = []
        yaml = ansiblelint.utils.parse_yaml_linenumbers(text)
        if yaml and hasattr(self, 'matchplay'):
            for play in yaml:
                result = self.matchplay(file, play)
                if result:
                    (section, message) = result
                    matches.append(Match(play[ansiblelint.utils.LINE_NUMBER_KEY], section,
                                   file['path'], self, message))
        return matches


class RulesCollection(object):

    def __init__(self):
        self.rules = []

    def register(self, obj):
        self.rules.append(obj)

    def __iter__(self):
        return iter(self.rules)

    def __len__(self):
        return len(self.rules)

    def extend(self, more):
        self.rules.extend(more)

    def run(self, playbookfile, tags=set(), skip_list=set()):
        text = ""
        matches = list()
        with open(playbookfile['path'], 'Ur') as f:
            text = f.read()
        for rule in self.rules:
            if not tags or not set(rule.tags).isdisjoint(tags):
                rule_definition = set(rule.tags)
                rule_definition.add(rule.id)
                if set(rule_definition).isdisjoint(skip_list):
                    matches.extend(rule.matchlines(playbookfile, text))
                    matches.extend(rule.matchtasks(playbookfile, text))
                    matches.extend(rule.matchyaml(playbookfile, text))

        return matches

    def __repr__(self):
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

    @classmethod
    def create_from_directory(cls, rulesdir):
        result = cls()
        result.rules = ansiblelint.utils.load_plugins(os.path.expanduser(rulesdir))
        return result


class Match:

    def __init__(self, linenumber, line, filename, rule, message=None):
        self.linenumber = linenumber
        self.line = line
        self.filename = filename
        self.rule = rule
        self.message = message or rule.shortdesc

    def __repr__(self):
        formatstr = "[{0}] ({1}) matched {2}:{3} {4}"
        return formatstr.format(self.rule.id, self.message,
                                self.filename, self.linenumber, self.line)


class Runner:

    def __init__(self, rules, playbooks, tags, skip_list, exclude_paths):
        self.rules = rules
        self.playbooks = set()
        for pb in playbooks:
            self.playbooks.add((pb, 'playbook'))
        self.tags = tags
        self.skip_list = skip_list
        self._update_exclude_paths(exclude_paths)

    def _update_exclude_paths(self, exclude_paths):
        if exclude_paths:
            # These will be (potentially) relative paths
            paths = [s.strip() for s in exclude_paths]
            # Since ansiblelint.utils.find_children returns absolute paths,
            # and the list of files we create in `Runner.run` can contain both
            # relative and absolute paths, we need to cover both bases.
            self.exclude_paths = paths + [os.path.abspath(p) for p in paths]
        else:
            self.exclude_paths = []

    def is_excluded(self, file_path):
        # Any will short-circuit as soon as something returns True, but will
        # be poor performance for the case where the path under question is
        # not excluded.
        return any(file_path.startswith(path) for path in self.exclude_paths)

    def run(self):
        files = list()
        for playbook in self.playbooks:
            if self.is_excluded(playbook[0]):
                continue
            files.append({'path': playbook[0], 'type': playbook[1]})
        visited = set()
        while (visited != self.playbooks):
            for arg in self.playbooks - visited:
                for file in ansiblelint.utils.find_children(arg):
                    if self.is_excluded(file['path']):
                        continue
                    self.playbooks.add((file['path'], file['type']))
                    files.append(file)
                visited.add(arg)

        matches = list()
        for file in files:
            matches.extend(self.rules.run(file, tags=set(self.tags),
                           skip_list=set(self.skip_list)))

        return matches
