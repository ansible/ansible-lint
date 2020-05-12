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
"""Main ansible-lint package."""

from collections import defaultdict
import logging
import os

from ansiblelint.rules import AnsibleLintRule  # noqa F401: exposing public API
import ansiblelint.utils
import ansiblelint.skip_utils

default_rulesdir = os.path.join(os.path.dirname(ansiblelint.utils.__file__), 'rules')
_logger = logging.getLogger(__name__)


class RulesCollection(object):

    def __init__(self, rulesdirs=None):
        """Initialize a RulesCollection instance."""
        if rulesdirs is None:
            rulesdirs = []
        self.rulesdirs = ansiblelint.utils.expand_paths_vars(rulesdirs)
        self.rules = []
        for rulesdir in self.rulesdirs:
            self.extend(ansiblelint.utils.load_plugins(rulesdir))

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

    def run(self, playbookfile, tags=set(), skip_list=frozenset()):
        text = ""
        matches = list()

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


class Runner(object):

    def __init__(self, rules, playbook, tags, skip_list, exclude_paths,
                 verbosity=0, checked_files=None):
        """Initialize a Runner instance."""
        self.rules = rules
        self.playbooks = set()
        # assume role if directory
        if os.path.isdir(playbook):
            self.playbooks.add((os.path.join(playbook, ''), 'role'))
            self.playbook_dir = playbook
        else:
            self.playbooks.add((playbook, 'playbook'))
            self.playbook_dir = os.path.dirname(playbook)
        self.tags = tags
        self.skip_list = skip_list
        self._update_exclude_paths(exclude_paths)
        self.verbosity = verbosity
        if checked_files is None:
            checked_files = set()
        self.checked_files = checked_files

    def _update_exclude_paths(self, exclude_paths):
        if exclude_paths:
            # These will be (potentially) relative paths
            paths = ansiblelint.utils.expand_paths_vars(exclude_paths)
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
            if playbook[1] == 'role':
                continue
            files.append({'path': ansiblelint.utils.normpath(playbook[0]),
                          'type': playbook[1],
                          # add an absolute path here, so rules are able to validate if
                          # referenced files exist
                          'absolute_directory': os.path.dirname(playbook[0])})
        visited = set()
        while (visited != self.playbooks):
            for arg in self.playbooks - visited:
                for child in ansiblelint.utils.find_children(arg, self.playbook_dir):
                    if self.is_excluded(child['path']):
                        continue
                    self.playbooks.add((child['path'], child['type']))
                    files.append(child)
                visited.add(arg)

        matches = list()

        # remove duplicates from files list
        files = [value for n, value in enumerate(files) if value not in files[:n]]

        # remove files that have already been checked
        files = [x for x in files if x['path'] not in self.checked_files]
        for file in files:
            _logger.debug(
                "Examining %s of type %s",
                ansiblelint.utils.normpath(file['path']),
                file['type'])
            matches.extend(self.rules.run(file, tags=set(self.tags),
                           skip_list=self.skip_list))
        # update list of checked files
        self.checked_files.update([x['path'] for x in files])

        return matches
