"""Tests for loaders submodule."""

import os
import tempfile
import uuid
from pathlib import Path
from textwrap import dedent

from ansiblelint.loaders import IGNORE_FILE, load_ignore_txt


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
                """,
                ),
            )

        cwd = Path.cwd()

        try:
            os.chdir(temporary_directory)
            result = load_ignore_txt()
        finally:
            os.chdir(cwd)

    assert result == {"playbook2.yml": {"package-latest", "foo-bar"}}


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
        "playbook.yml": {"more-foo", "foo-bar"},
        "tasks/main.yml": {"more-bar"},
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
                    vars/main.yml tuco
                    roles/guzman/tasks/main.yml lalo
                    roles/eduardo/tasks/main.yml lalo
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
        "playbook.yml": {"hector"},
        "roles/eduardo/tasks/main.yml": {"lalo"},
        "roles/guzman/tasks/main.yml": {"lalo"},
        "vars/main.yml": {"tuco"},
    }


def test_load_ignore_txt_custom_fail() -> None:
    """Test load_ignore_txt with a user defined but invalid ignore-file location."""
    result = load_ignore_txt(Path(str(uuid.uuid4())))

    assert not result
