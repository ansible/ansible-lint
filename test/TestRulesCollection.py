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

import collections
import unittest

from ansiblelint import RulesCollection


class TestRulesCollection(unittest.TestCase):

    rules = None
    ematchtestfile = dict(path='test/ematchtest.yml', type='playbook')
    bracketsmatchtestfile = dict(path='test/bracketsmatchtest.yml', type='playbook')

    def setUp(self):
        self.rules = RulesCollection.create_from_directory('./test/rules')

    def test_load_collection_from_directory(self):
        self.assertEqual(len(self.rules), 2)

    def test_run_collection(self):
        matches = self.rules.run(self.ematchtestfile)
        self.assertEqual(len(matches), 3)

    def test_tags(self):
        matches = self.rules.run(self.ematchtestfile, tags=['test1'])
        self.assertEqual(len(matches), 3)
        matches = self.rules.run(self.ematchtestfile, tags=['test2'])
        self.assertEqual(len(matches), 0)
        matches = self.rules.run(self.bracketsmatchtestfile, tags=['test1'])
        self.assertEqual(len(matches), 1)
        matches = self.rules.run(self.bracketsmatchtestfile, tags=['test2'])
        self.assertEqual(len(matches), 2)

    def test_skip_tags(self):
        matches = self.rules.run(self.ematchtestfile, skip_list=['test1'])
        self.assertEqual(len(matches), 0)
        matches = self.rules.run(self.ematchtestfile, skip_list=['test2'])
        self.assertEqual(len(matches), 3)
        matches = self.rules.run(self.bracketsmatchtestfile, skip_list=['test1'])
        self.assertEqual(len(matches), 2)
        matches = self.rules.run(self.bracketsmatchtestfile, skip_list=['test2'])
        self.assertEqual(len(matches), 1)

    def test_skip_id(self):
        matches = self.rules.run(self.ematchtestfile, skip_list=['TEST0001'])
        self.assertEqual(len(matches), 0)
        matches = self.rules.run(self.ematchtestfile, skip_list=['TEST0002'])
        self.assertEqual(len(matches), 3)
        matches = self.rules.run(self.bracketsmatchtestfile, skip_list=['TEST0001'])
        self.assertEqual(len(matches), 2)
        matches = self.rules.run(self.bracketsmatchtestfile, skip_list=['TEST0002'])
        self.assertEqual(len(matches), 1)

    def test_skip_non_existent_id(self):
        matches = self.rules.run(self.ematchtestfile, skip_list=['DOESNOTEXIST'])
        self.assertEqual(len(matches), 3)

    def test_no_duplicate_rule_ids(self):
        real_rules = RulesCollection.create_from_directory('./lib/ansiblelint/rules')
        rule_ids = [ rule.id for rule in real_rules ]
        self.assertEqual([x for x, y in collections.Counter(rule_ids).items() if y > 1], [])
