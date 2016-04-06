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

import os
import unittest

import ansiblelint
from ansiblelint import RulesCollection
from ansiblelint.formatters import Formatter


class TestRule(unittest.TestCase):

    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection.create_from_directory(rulesdir)

    def test_runner_count(self):
        filename = 'test/nomatchestest.yml'
        runner = ansiblelint.Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 0)

    def test_unicode_runner_count(self):
        filename = 'test/unicode.yml'
        runner = ansiblelint.Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 1)

    def test_unicode_formatting(self):
        filename = 'test/unicode.yml'
        runner = ansiblelint.Runner(self.rules, filename, [], [], [])
        matches = runner.run()
        formatter = Formatter()
        formatter.format(matches[0])

    def test_runner_excludes_paths(self):
        filename = 'examples/lots_of_warnings.yml'
        excludes = ['examples/lots_of_warnings.yml']
        runner = ansiblelint.Runner(self.rules, filename, [], [], excludes)
        assert (len(runner.run()) == 0)

    def test_runner_block_count(self):
        filename = 'test/block.yml'
        runner = ansiblelint.Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 0)

    def test_runner_become_count(self):
        filename = 'test/become.yml'
        runner = ansiblelint.Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 0)

    def test_runner_empty_tags_count(self):
        filename = 'test/emptytags.yml'
        runner = ansiblelint.Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 0)
