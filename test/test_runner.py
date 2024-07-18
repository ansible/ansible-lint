"""Tests for runner submodule."""

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
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from ansiblelint import formatters
from ansiblelint.file_utils import Lintable
from ansiblelint.runner import Runner

if TYPE_CHECKING:
    from ansiblelint.rules import RulesCollection

LOTS_OF_WARNINGS_PLAYBOOK = Path("examples/playbooks/lots_of_warnings.yml").resolve()


@pytest.mark.parametrize(
    ("playbook", "exclude", "length"),
    (
        pytest.param(
            Path("examples/playbooks/nomatchestest.yml"),
            [],
            0,
            id="nomatchestest",
        ),
        pytest.param(Path("examples/playbooks/unicode.yml"), [], 1, id="unicode"),
        pytest.param(
            LOTS_OF_WARNINGS_PLAYBOOK,
            [LOTS_OF_WARNINGS_PLAYBOOK],
            993,
            id="lots_of_warnings",
        ),
        pytest.param(Path("examples/playbooks/become.yml"), [], 0, id="become"),
        pytest.param(
            Path("examples/playbooks/contains_secrets.yml"),
            [],
            0,
            id="contains_secrets",
        ),
    ),
)
def test_runner(
    default_rules_collection: RulesCollection,
    playbook: Path,
    exclude: list[str],
    length: int,
) -> None:
    """Test that runner can go through any corner cases."""
    runner = Runner(playbook, rules=default_rules_collection, exclude_paths=exclude)

    matches = runner.run()

    assert len(matches) == length


def test_runner_exclude_paths(default_rules_collection: RulesCollection) -> None:
    """Test that exclude paths do work."""
    runner = Runner(
        "examples/playbooks/deep/",
        rules=default_rules_collection,
        exclude_paths=["examples/playbooks/deep/empty.yml"],
    )

    matches = runner.run()
    assert len(matches) == 0


@pytest.mark.parametrize(
    ("exclude_path"),
    (pytest.param("**/playbooks_globs/*b.yml", id="1"),),
)
def test_runner_exclude_globs(
    default_rules_collection: RulesCollection,
    exclude_path: str,
) -> None:
    """Test that globs work."""
    runner = Runner(
        "examples/playbooks_globs",
        rules=default_rules_collection,
        exclude_paths=[exclude_path],
    )

    matches = runner.run()
    assert len(matches) == 0


@pytest.mark.parametrize(
    ("formatter_cls"),
    (
        pytest.param(formatters.Formatter, id="Formatter-plain"),
        pytest.param(formatters.ParseableFormatter, id="ParseableFormatter-colored"),
        pytest.param(formatters.QuietFormatter, id="QuietFormatter-colored"),
        pytest.param(formatters.Formatter, id="Formatter-colored"),
    ),
)
def test_runner_unicode_format(
    default_rules_collection: RulesCollection,
    formatter_cls: type[formatters.BaseFormatter[Any]],
) -> None:
    """Check that all formatters are unicode-friendly."""
    formatter = formatter_cls(Path.cwd(), display_relative_path=True)
    runner = Runner(
        Lintable("examples/playbooks/unicode.yml", kind="playbook"),
        rules=default_rules_collection,
    )

    matches = runner.run()

    formatter.apply(matches[0])


@pytest.mark.parametrize(
    "directory_name",
    (
        pytest.param(Path("test/fixtures/verbosity-tests"), id="rel"),
        pytest.param(Path("test/fixtures/verbosity-tests").resolve(), id="abs"),
    ),
)
def test_runner_with_directory(
    default_rules_collection: RulesCollection,
    directory_name: Path,
) -> None:
    """Check that runner detects a directory as role."""
    runner = Runner(directory_name, rules=default_rules_collection)

    expected = Lintable(name=directory_name, kind="role")
    assert expected in runner.lintables


def test_files_not_scanned_twice(default_rules_collection: RulesCollection) -> None:
    """Ensure that lintables aren't double-checked."""
    checked_files: set[Lintable] = set()

    filename = Path("examples/playbooks/common-include-1.yml").resolve()
    runner = Runner(
        filename,
        rules=default_rules_collection,
        verbosity=0,
        checked_files=checked_files,
    )
    run1 = runner.run()
    assert len(runner.checked_files) == 2
    assert len(run1) == 1

    filename = Path("examples/playbooks/common-include-2.yml").resolve()
    runner = Runner(
        str(filename),
        rules=default_rules_collection,
        verbosity=0,
        checked_files=checked_files,
    )
    run2 = runner.run()
    assert len(runner.checked_files) == 3
    # this second run should return 0 because the included filed was already
    # processed and added to checked_files, which acts like a bypass list.
    assert len(run2) == 0


@pytest.mark.parametrize(
    ("filename", "failures", "checked_files_no"),
    (
        pytest.param(
            "examples/playbooks/common-include-wrong-syntax.yml",
            1,
            1,
            id="1",
        ),
        pytest.param(
            "examples/playbooks/common-include-wrong-syntax2.yml",
            1,
            1,
            id="2",
        ),
        pytest.param(
            "examples/playbooks/common-include-wrong-syntax3.yml",
            0,
            2,
            id="3",
        ),
    ),
)
def test_include_wrong_syntax(
    filename: str,
    failures: int,
    checked_files_no: int,
    default_rules_collection: RulesCollection,
) -> None:
    """Ensure that lintables aren't double-checked."""
    checked_files: set[Lintable] = set()

    path = Path(filename).resolve()
    runner = Runner(
        path,
        rules=default_rules_collection,
        verbosity=0,
        checked_files=checked_files,
    )
    result = runner.run()
    assert len(runner.checked_files) == checked_files_no
    assert len(result) == failures, result
    for item in result:
        assert item.tag == "syntax-check[no-file]"


def test_runner_not_found(default_rules_collection: RulesCollection) -> None:
    """Ensure that lintables aren't double-checked."""
    checked_files: set[Lintable] = set()

    filename = Path("this/folder/does/not/exist").resolve()
    runner = Runner(
        filename,
        rules=default_rules_collection,
        verbosity=0,
        checked_files=checked_files,
    )
    result = runner.run()
    assert len(runner.checked_files) == 1
    assert len(result) == 1
    assert result[0].tag == "load-failure[not-found]"


def test_runner_tmp_file(
    tmp_path: Path,
    default_rules_collection: RulesCollection,
) -> None:
    """Ensure we do not ignore an explicit temporary file from linting."""
    # https://github.com/ansible/ansible-lint/issues/2628
    filename = tmp_path / "playbook.yml"
    filename.write_text("---\n")
    runner = Runner(
        filename,
        rules=default_rules_collection,
        verbosity=0,
    )
    result = runner.run()
    assert len(result) == 1
    assert result[0].tag == "syntax-check[empty-playbook]"


def test_with_full_path(default_rules_collection: RulesCollection) -> None:
    """Ensure that lintables include file path starting from home directory."""
    filename = Path("examples/playbooks/deep").absolute()
    runner = Runner(
        filename,
        rules=default_rules_collection,
        verbosity=0,
    )
    result = runner.run()
    assert len(result) == 1
    assert result[0].tag == "name[casing]"
