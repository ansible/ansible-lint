"""Tests for loaders submodule."""

import os
import tempfile
import uuid
from pathlib import Path
from textwrap import dedent

import pytest

from ansiblelint.loaders import (
    IGNORE_FILE,
    IgnoreRule,
    IgnoreRuleQualifier,
    load_ignore_txt,
)


def test_load_ignore_txt_default_empty() -> None:
    """Test load_ignore_txt when no ignore-file is present."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        cwd = Path.cwd()

        try:
            os.chdir(temporary_directory)
            result = load_ignore_txt()
        finally:
            os.chdir(cwd)

    assert not result


def test_load_ignore_txt_default_success() -> None:
    """Test load_ignore_txt with an existing ignore-file in the default location."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        ignore_file = Path(temporary_directory) / IGNORE_FILE.default

        with ignore_file.open("w", encoding="utf-8") as _ignore_file:
            _ignore_file.write(
                dedent(
                    """
                    # See https://ansible.readthedocs.io/projects/lint/configuring/#ignoring-rules-for-entire-files
                    playbook2.yml package-latest # comment
                    playbook2.yml foo-bar
                    playbook2.yml another-role skip # rule with qualifier
                """,
                ),
            )

        cwd = Path.cwd()

        try:
            os.chdir(temporary_directory)
            result = load_ignore_txt()
        finally:
            os.chdir(cwd)

    assert result == {
        "playbook2.yml": {
            IgnoreRule("package-latest", frozenset()),
            IgnoreRule("foo-bar", frozenset()),
            IgnoreRule("another-role", frozenset([IgnoreRuleQualifier.SKIP])),
        }
    }


def test_load_ignore_txt_default_success_alternative() -> None:
    """Test load_ignore_txt with an ignore-file in the alternative location ('.config' subdirectory)."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        ignore_file = Path(temporary_directory) / IGNORE_FILE.alternative
        ignore_file.parent.mkdir(parents=True)

        with ignore_file.open("w", encoding="utf-8") as _ignore_file:
            _ignore_file.write(
                dedent(
                    """
                    playbook.yml foo-bar
                    playbook.yml more-foo # what-the-foo?
                    tasks/main.yml more-bar
                """,
                ),
            )

        cwd = Path.cwd()

        try:
            os.chdir(temporary_directory)
            result = load_ignore_txt()
        finally:
            os.chdir(cwd)

    assert result == {
        "playbook.yml": {
            IgnoreRule("more-foo", frozenset()),
            IgnoreRule("foo-bar", frozenset()),
        },
        "tasks/main.yml": {IgnoreRule("more-bar", frozenset())},
    }


def test_load_ignore_txt_custom_success() -> None:
    """Test load_ignore_txt with an ignore-file in a user defined location."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        ignore_file = Path(temporary_directory) / "subdir" / "my_ignores.txt"
        ignore_file.parent.mkdir(parents=True, exist_ok=True)

        with ignore_file.open("w", encoding="utf-8") as _ignore_file:
            _ignore_file.write(
                dedent(
                    """
                    playbook.yml hector
                    vars/main.yml alpha
                    roles/guzman/tasks/main.yml foo
                    roles/eduardo/tasks/main.yml foo
                """,
                ),
            )

        cwd = Path.cwd()

        try:
            os.chdir(temporary_directory)
            result = load_ignore_txt(Path(ignore_file))
        finally:
            os.chdir(cwd)

    assert result == {
        "playbook.yml": {IgnoreRule("hector", frozenset())},
        "roles/eduardo/tasks/main.yml": {IgnoreRule("foo", frozenset())},
        "roles/guzman/tasks/main.yml": {IgnoreRule("foo", frozenset())},
        "vars/main.yml": {IgnoreRule("alpha", frozenset())},
    }


def test_load_ignore_txt_custom_fail() -> None:
    """Test load_ignore_txt with a user defined but invalid ignore-file location."""
    result = load_ignore_txt(Path(str(uuid.uuid4())))

    assert not result


def test_load_ignore_txt_invalid_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test load_ignore_txt with an existing ignore-file in the default location."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        ignore_file = Path(temporary_directory) / IGNORE_FILE.default

        with ignore_file.open("w", encoding="utf-8") as _ignore_file:
            _ignore_file.write(
                dedent(
                    """
                    playbook2.yml package-latest invalid-tag
                """,
                ),
            )

        monkeypatch.chdir(temporary_directory)
        with pytest.raises(RuntimeError, match="Unable to parse line"):
            load_ignore_txt()
