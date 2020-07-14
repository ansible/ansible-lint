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

import pytest

from ansiblelint import formatters
from ansiblelint.cli import abspath
from ansiblelint.runner import Runner

LOTS_OF_WARNINGS_PLAYBOOK = abspath('examples/lots_of_warnings.yml', os.getcwd())


@pytest.mark.parametrize(('playbook', 'exclude', 'length'), (
    ('test/nomatchestest.yml', [], 0),
    ('test/unicode.yml', [], 1),
    (LOTS_OF_WARNINGS_PLAYBOOK, [LOTS_OF_WARNINGS_PLAYBOOK], 0),
    ('test/block.yml', [], 0),
    ('test/become.yml', [], 0),
    ('test/emptytags.yml', [], 0),
    ('test/contains_secrets.yml', [], 0),
))
def test_runner(default_rules_collection, playbook, exclude, length):
    runner = Runner(default_rules_collection, playbook, [], [], exclude)

    matches = runner.run()

    assert len(matches) == length


@pytest.mark.parametrize(('formatter_cls', 'format_kwargs'), (
    pytest.param(formatters.Formatter, {}, id='Formatter-plain'),
    pytest.param(formatters.ParseableFormatter,
                 {'colored': True},
                 id='ParseableFormatter-colored'),
    pytest.param(formatters.QuietFormatter,
                 {'colored': True},
                 id='QuietFormatter-colored'),
    pytest.param(formatters.Formatter,
                 {'colored': True},
                 id='Formatter-colored'),
))
def test_runner_unicode_format(default_rules_collection, formatter_cls, format_kwargs):
    formatter = formatter_cls(os.getcwd(), True)
    runner = Runner(default_rules_collection, 'test/unicode.yml', [], [], [])

    matches = runner.run()

    formatter.format(matches[0], **format_kwargs)


@pytest.mark.parametrize('directory_name', ('test/', os.path.abspath('test')))
def test_runner_with_directory(default_rules_collection, directory_name):
    runner = Runner(default_rules_collection, directory_name, [], [], [])
    assert list(runner.playbooks)[0][1] == 'role'


def test_files_not_scanned_twice(default_rules_collection):
    checked_files = set()

    filename = os.path.abspath('test/common-include-1.yml')
    runner = Runner(default_rules_collection, filename, [], [], [], 0, checked_files)
    run1 = runner.run()

    filename = os.path.abspath('test/common-include-2.yml')
    runner = Runner(default_rules_collection, filename, [], [], [], 0, checked_files)
    run2 = runner.run()

    assert (len(run1) + len(run2)) == 1
