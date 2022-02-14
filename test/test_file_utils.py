"""Tests for file utility functions."""
import os
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, Union

import pytest
from _pytest.capture import CaptureFixture
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from ansiblelint import cli, file_utils
from ansiblelint.__main__ import initialize_logger
from ansiblelint.constants import FileType
from ansiblelint.file_utils import (
    Lintable,
    expand_path_vars,
    expand_paths_vars,
    guess_project_dir,
    normpath,
)

from .conftest import cwd


@pytest.mark.parametrize(
    "path",
    (
        pytest.param(Path("a/b/../"), id="pathlib.Path"),
        pytest.param("a/b/../", id="str"),
    ),
)
def test_normpath_with_path_object(path: str) -> None:
    """Ensure that relative parent dirs are normalized in paths."""
    assert normpath(path) == "a"


def test_expand_path_vars(monkeypatch: MonkeyPatch) -> None:
    """Ensure that tilde and env vars are expanded in paths."""
    test_path = "/test/path"
    monkeypatch.setenv("TEST_PATH", test_path)
    assert expand_path_vars("~") == os.path.expanduser("~")
    assert expand_path_vars("$TEST_PATH") == test_path


@pytest.mark.parametrize(
    ("test_path", "expected"),
    (
        pytest.param(Path("$TEST_PATH"), "/test/path", id="pathlib.Path"),
        pytest.param("$TEST_PATH", "/test/path", id="str"),
        pytest.param("  $TEST_PATH  ", "/test/path", id="stripped-str"),
        pytest.param("~", os.path.expanduser("~"), id="home"),
    ),
)
def test_expand_paths_vars(
    test_path: Union[str, Path], expected: str, monkeypatch: MonkeyPatch
) -> None:
    """Ensure that tilde and env vars are expanded in paths lists."""
    monkeypatch.setenv("TEST_PATH", "/test/path")
    assert expand_paths_vars([test_path]) == [expected]  # type: ignore


@pytest.mark.parametrize(
    ("reset_env_var", "message_prefix"),
    (
        # simulate absence of git command
        ("PATH", "Failed to locate command: "),
        # simulate a missing git repo
        ("GIT_DIR", "Looking up for files"),
    ),
    ids=("no-git-cli", "outside-git-repo"),
)
def test_discover_lintables_git_verbose(
    reset_env_var: str,
    message_prefix: str,
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
) -> None:
    """Ensure that autodiscovery lookup failures are logged."""
    options = cli.get_config(["-v"])
    initialize_logger(options.verbosity)
    monkeypatch.setenv(reset_env_var, "")
    file_utils.discover_lintables(options)

    assert any(m[2].startswith("Looking up for files") for m in caplog.record_tuples)
    assert any(m.startswith(message_prefix) for m in caplog.messages)


@pytest.mark.parametrize(
    "is_in_git",
    (True, False),
    ids=("in Git", "outside Git"),
)
def test_discover_lintables_silent(
    is_in_git: bool, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Verify that no stderr output is displayed while discovering yaml files.

    (when the verbosity is off, regardless of the Git or Git-repo presence)

    Also checks expected number of files are detected.
    """
    options = cli.get_config([])
    test_dir = Path(__file__).resolve().parent
    lint_path = test_dir / ".." / "examples" / "roles" / "test-role"
    if not is_in_git:
        monkeypatch.setenv("GIT_DIR", "")

    yaml_count = len(list(lint_path.glob("**/*.yml"))) + len(
        list(lint_path.glob("**/*.yaml"))
    )

    monkeypatch.chdir(str(lint_path))
    files = file_utils.discover_lintables(options)
    stderr = capsys.readouterr().err
    assert not stderr, "No stderr output is expected when the verbosity is off"
    assert (
        len(files) == yaml_count
    ), "Expected to find {yaml_count} yaml files in {lint_path}".format_map(
        locals(),
    )


def test_discover_lintables_umlaut(monkeypatch: MonkeyPatch) -> None:
    """Verify that filenames containing German umlauts are not garbled by the discover_lintables."""
    options = cli.get_config([])
    test_dir = Path(__file__).resolve().parent
    lint_path = test_dir / ".." / "examples" / "playbooks"

    monkeypatch.chdir(str(lint_path))
    files = file_utils.discover_lintables(options)
    assert '"with-umlaut-\\303\\244.yml"' not in files
    assert "with-umlaut-ä.yml" in files


@pytest.mark.parametrize(
    ("path", "kind"),
    (
        ("foo/playbook.yml", "playbook"),
        ("playbooks/foo.yml", "playbook"),
        ("playbooks/roles/foo.yml", "yaml"),
        # the only yml file that is not a playbook inside molecule/ folders
        (".config/molecule/config.yml", "yaml"),  # molecule shared config
        (
            "roles/foo/molecule/scenario1/base.yml",
            "yaml",
        ),  # molecule scenario base config
        (
            "roles/foo/molecule/scenario1/molecule.yml",
            "yaml",
        ),  # molecule scenario config
        ("roles/foo/molecule/scenario2/foobar.yml", "playbook"),  # custom playbook name
        (
            "roles/foo/molecule/scenario3/converge.yml",
            "playbook",
        ),  # common playbook name
        (
            "roles/foo/molecule/scenario3/requirements.yml",
            "requirements",
        ),  # requirements
        (
            "roles/foo/molecule/scenario3/collections.yml",
            "requirements",
        ),  # requirements
        # tasks files:
        ("tasks/directory with spaces/main.yml", "tasks"),  # tasks
        ("tasks/requirements.yml", "tasks"),  # tasks
        # requirements (we do not support includes yet)
        ("requirements.yml", "requirements"),  # collection requirements
        ("roles/foo/meta/requirements.yml", "requirements"),  # inside role requirements
        # Undeterminable files:
        ("test/fixtures/unknown-type.yml", "yaml"),
        ("releasenotes/notes/run-playbooks-refactor.yaml", "reno"),  # reno
        ("examples/host_vars/localhost.yml", "vars"),
        ("examples/group_vars/all.yml", "vars"),
        ("examples/playbooks/vars/other.yml", "vars"),
        ("examples/playbooks/vars/subfolder/settings.yml", "vars"),  # deep vars
        ("molecule/scenario/collections.yml", "requirements"),  # deprecated 2.8 format
        (
            "../roles/geerlingguy.mysql/tasks/configure.yml",
            "tasks",
        ),  # relative path involved
        ("galaxy.yml", "galaxy"),
        ("foo.j2.yml", "jinja2"),
        ("foo.yml.j2", "jinja2"),
        ("foo.j2.yaml", "jinja2"),
        ("foo.yaml.j2", "jinja2"),
    ),
)
def test_default_kinds(monkeypatch: MonkeyPatch, path: str, kind: FileType) -> None:
    """Verify auto-detection logic based on DEFAULT_KINDS."""
    options = cli.get_config([])

    def mockreturn(options: Namespace) -> Dict[str, Any]:
        return {path: kind}

    # assert Lintable is able to determine file type
    lintable_detected = Lintable(path)
    lintable_expected = Lintable(path, kind=kind)
    assert lintable_detected == lintable_expected

    monkeypatch.setattr(file_utils, "discover_lintables", mockreturn)
    result = file_utils.discover_lintables(options)
    # get_lintable could return additional files and we only care to see
    # that the given file is among the returned list.
    assert lintable_detected.name in result
    assert lintable_detected.kind == result[lintable_expected.name]


def test_guess_project_dir(tmp_path: Path) -> None:
    """Verify guess_project_dir()."""
    with cwd(str(tmp_path)):
        result = guess_project_dir(None)
        assert result == str(tmp_path)
