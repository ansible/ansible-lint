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
from typing import Any, List, Set, Type

import pytest

from ansiblelint import formatters
from ansiblelint.cli import abspath
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner

LOTS_OF_WARNINGS_PLAYBOOK = abspath(
    'examples/playbooks/lots_of_warnings.yml', os.getcwd()
)


@pytest.mark.parametrize(
    ('playbook', 'exclude', 'length'),
    (
        pytest.param('examples/playbooks/nomatchestest.yml', [], 0, id="nomatchestest"),
        pytest.param('examples/playbooks/unicode.yml', [], 1, id="unicode"),
        pytest.param(
            LOTS_OF_WARNINGS_PLAYBOOK,
            [LOTS_OF_WARNINGS_PLAYBOOK],
            0,
            id="lots_of_warnings",
        ),
        pytest.param('examples/playbooks/become.yml', [], 0, id="become"),
        pytest.param(
            'examples/playbooks/contains_secrets.yml', [], 0, id="contains_secrets"
        ),
    ),
)
def test_runner(
    default_rules_collection: RulesCollection,
    playbook: str,
    exclude: List[str],
    length: int,
) -> None:
    """Test that runner can go through any corner cases."""
    runner = Runner(playbook, rules=default_rules_collection, exclude_paths=exclude)

    matches = runner.run()

    assert len(matches) == length


def test_runner_exclude_paths(default_rules_collection: RulesCollection) -> None:
    """Test that exclude paths do work."""
    runner = Runner(
        'examples/playbooks/example.yml',
        rules=default_rules_collection,
        exclude_paths=['examples/'],
    )

    matches = runner.run()
    assert len(matches) == 0


@pytest.mark.parametrize(('exclude_path'), ('**/playbooks/*.yml',))
def test_runner_exclude_globs(
    default_rules_collection: RulesCollection, exclude_path: str
) -> None:
    """Test that globs work."""
    runner = Runner(
        'examples/playbooks',
        rules=default_rules_collection,
        exclude_paths=[exclude_path],
    )

    matches = runner.run()
    # we expect to find one error from the only .yaml file we have there.
    assert len(matches) == 1


@pytest.mark.parametrize(
    ('formatter_cls'),
    (
        pytest.param(formatters.Formatter, id='Formatter-plain'),
        pytest.param(formatters.ParseableFormatter, id='ParseableFormatter-colored'),
        pytest.param(formatters.QuietFormatter, id='QuietFormatter-colored'),
        pytest.param(formatters.Formatter, id='Formatter-colored'),
    ),
)
def test_runner_unicode_format(
    default_rules_collection: RulesCollection,
    formatter_cls: Type[formatters.BaseFormatter[Any]],
) -> None:
    """Check that all formatters are unicode-friendly."""
    formatter = formatter_cls(os.getcwd(), display_relative_path=True)
    runner = Runner(
        Lintable('examples/playbooks/unicode.yml', "playbook"),
        rules=default_rules_collection,
    )

    matches = runner.run()

    formatter.format(matches[0])


@pytest.mark.parametrize('directory_name', ('test/', os.path.abspath('test')))
def test_runner_with_directory(
    default_rules_collection: RulesCollection, directory_name: str
) -> None:
    """Check that runner detects a directory as role."""
    runner = Runner(directory_name, rules=default_rules_collection)

    expected = Lintable(name=directory_name, kind="role")
    assert expected in runner.lintables


def test_files_not_scanned_twice(default_rules_collection: RulesCollection) -> None:
    """Ensure that lintables aren't double-checked."""
    checked_files: Set[Lintable] = set()

    filename = os.path.abspath('examples/playbooks/common-include-1.yml')
    runner = Runner(
        filename,
        rules=default_rules_collection,
        verbosity=0,
        checked_files=checked_files,
    )
    run1 = runner.run()
    assert len(runner.checked_files) == 2
    assert len(run1) == 1

    filename = os.path.abspath('examples/playbooks/common-include-2.yml')
    runner = Runner(
        filename,
        rules=default_rules_collection,
        verbosity=0,
        checked_files=checked_files,
    )
    run2 = runner.run()
    assert len(runner.checked_files) == 3
    # this second run should return 0 because the included filed was already
    # processed and added to checked_files, which acts like a bypass list.
    assert len(run2) == 0
