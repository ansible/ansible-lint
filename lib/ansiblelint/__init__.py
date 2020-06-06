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

from ansiblelint.rules import AnsibleLintRule  # noqa F401: exposing public API
import ansiblelint.utils
import ansiblelint.skip_utils
from typing import List


_logger = logging.getLogger(__name__)


class RulesCollection(object):

    def __init__(self, rulesdirs=None):
        """Initialize a RulesCollection instance."""
        if rulesdirs is None:
            rulesdirs = []
        self.rulesdirs = ansiblelint.utils.expand_paths_vars(rulesdirs)
        self.rules = []
        for rulesdir in self.rulesdirs:
            _logger.debug("Loading rules from %s", rulesdir)
            self.extend(ansiblelint.utils.load_plugins(rulesdir))
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
