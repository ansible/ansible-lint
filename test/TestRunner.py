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
from ansiblelint import Runner, RulesCollection
import ansiblelint.formatters


class TestRule(unittest.TestCase):

    def setUp(self):
        rulesdir = os.path.join('lib', 'ansiblelint', 'rules')
        self.rules = RulesCollection.create_from_directory(rulesdir)

    def test_runner_count(self):
        filename = 'test/nomatchestest.yml'
        runner = Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 0)

    def test_unicode_runner_count(self):
        filename = 'test/unicode.yml'
        runner = Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 1)

    def test_unicode_standard_formatting(self):
        filename = 'test/unicode.yml'
        runner = Runner(self.rules, filename, [], [], [])
        matches = runner.run()
        formatter = ansiblelint.formatters.Formatter()
        formatter.format(matches[0])

    def test_unicode_parseable_colored_formatting(self):
        filename = 'test/unicode.yml'
        runner = Runner(self.rules, filename, [], [], [])
        matches = runner.run()
        formatter = ansiblelint.formatters.ParseableFormatter()
        formatter.format(matches[0], colored=True)

    def test_unicode_quiet_colored_formatting(self):
        filename = 'test/unicode.yml'
        runner = Runner(self.rules, filename, [], [], [])
        matches = runner.run()
        formatter = ansiblelint.formatters.QuietFormatter()
        formatter.format(matches[0], colored=True)

    def test_unicode_standard_color_formatting(self):
        filename = 'test/unicode.yml'
        runner = Runner(self.rules, filename, [], [], [])
        matches = runner.run()
        formatter = ansiblelint.formatters.Formatter()
        formatter.format(matches[0], colored=True)

    def test_runner_excludes_paths(self):
        filename = 'examples/lots_of_warnings.yml'
        excludes = ['examples/lots_of_warnings.yml']
        runner = Runner(self.rules, filename, [], [], excludes)
        assert (len(runner.run()) == 0)

    def test_runner_block_count(self):
        filename = 'test/block.yml'
        runner = Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 0)

    def test_runner_become_count(self):
        filename = 'test/become.yml'
        runner = Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 0)

    def test_runner_empty_tags_count(self):
        filename = 'test/emptytags.yml'
        runner = Runner(self.rules, filename, [], [], [])
        assert (len(runner.run()) == 0)

    def test_runner_encrypted_secrets(self):
        from pkg_resources import parse_version
        import ansible
        # Only run this test for ansible 2.3+
        # It checks ansible-lint's parsing of yaml files that contain
        # encrypted secrets.
        if parse_version(ansible.__version__) >= parse_version('2.3'):
            filename = 'test/contains_secrets.yml'
            runner = Runner(self.rules, filename, [], [], [])
            assert (len(runner.run()) == 0)

    def test_dir_with_trailing_slash(self):
        filename = 'test/'
        runner = Runner(self.rules, filename, [], [], [])
        assert (list(runner.playbooks)[0][1] == 'role')

    def test_dir_with_fullpath(self):
        filename = os.path.abspath('test')
        runner = Runner(self.rules, filename, [], [], [])
        assert (list(runner.playbooks)[0][1] == 'role')

    def test_files_not_scanned_twice(self):
        checked_files = set()

        filename = os.path.abspath('test/common-include-1.yml')
        runner = Runner(self.rules, filename, [], [], [], 0, checked_files)
        run1 = runner.run()

        filename = os.path.abspath('test/common-include-2.yml')
        runner = Runner(self.rules, filename, [], [], [], 0, checked_files)
        run2 = runner.run()

        assert ((len(run1) + len(run2)) == 1)
