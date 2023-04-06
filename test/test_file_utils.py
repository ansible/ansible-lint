"""Tests for file utility functions."""
from __future__ import annotations

import os
import time
from argparse import Namespace
from pathlib import Path
from typing import Any

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
    normpath_path,
)
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner

from .conftest import cwd


@pytest.mark.parametrize(
    ("path", "expected"),
    (
        pytest.param(Path("a/b/../"), "a", id="pathlib.Path"),
        pytest.param("a/b/../", "a", id="str"),
        pytest.param("", ".", id="empty"),
        pytest.param(".", ".", id="empty"),
    ),
)
def test_normpath(path: str, expected: str) -> None:
    """Ensure that relative parent dirs are normalized in paths."""
    assert normpath(path) == expected


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
    test_path: str | Path, expected: str, monkeypatch: MonkeyPatch
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
        pytest.param("tasks/run_test_playbook.yml", "tasks", id="0"),
        pytest.param("foo/playbook.yml", "playbook", id="1"),
        pytest.param("playbooks/foo.yml", "playbook", id="2"),
        pytest.param("examples/roles/foo.yml", "yaml", id="3"),
        # the only yml file that is not a playbook inside molecule/ folders
        pytest.param(
            "examples/.config/molecule/config.yml", "yaml", id="4"
        ),  # molecule shared config
        pytest.param(
            "test/schemas/test/molecule/cluster/base.yml", "yaml", id="5"
        ),  # molecule scenario base config
        pytest.param(
            "test/schemas/test/molecule/cluster/molecule.yml", "yaml", id="6"
        ),  # molecule scenario config
        pytest.param(
            "test/schemas/test/molecule/cluster/foobar.yml", "playbook", id="7"
        ),  # custom playbook name
        pytest.param(
            "test/schemas/test/molecule/cluster/converge.yml", "playbook", id="8"
        ),  # common playbook name
        pytest.param(
            "roles/foo/molecule/scenario3/requirements.yml", "requirements", id="9"
        ),  # requirements
        pytest.param(
            "roles/foo/molecule/scenario3/collections.yml", "requirements", id="10"
        ),  # requirements
        pytest.param(
            "roles/foo/meta/argument_specs.yml", "role-arg-spec", id="11"
        ),  # role argument specs
        # tasks files:
        pytest.param("tasks/directory with spaces/main.yml", "tasks", id="12"),  # tasks
        pytest.param("tasks/requirements.yml", "tasks", id="13"),  # tasks
        # requirements (we do not support includes yet)
        pytest.param(
            "requirements.yml", "requirements", id="14"
        ),  # collection requirements
        pytest.param(
            "roles/foo/meta/requirements.yml", "requirements", id="15"
        ),  # inside role requirements
        # Undeterminable files:
        pytest.param("test/fixtures/unknown-type.yml", "yaml", id="16"),
        pytest.param(
            "releasenotes/notes/run-playbooks-refactor.yaml", "reno", id="17"
        ),  # reno
        pytest.param("examples/host_vars/localhost.yml", "vars", id="18"),
        pytest.param("examples/group_vars/all.yml", "vars", id="19"),
        pytest.param("examples/playbooks/vars/other.yml", "vars", id="20"),
        pytest.param(
            "examples/playbooks/vars/subfolder/settings.yml", "vars", id="21"
        ),  # deep vars
        pytest.param(
            "molecule/scenario/collections.yml", "requirements", id="22"
        ),  # deprecated 2.8 format
        pytest.param(
            "../roles/geerlingguy.mysql/tasks/configure.yml", "tasks", id="23"
        ),  # relative path involved
        pytest.param("galaxy.yml", "galaxy", id="24"),
        pytest.param("foo.j2.yml", "jinja2", id="25"),
        pytest.param("foo.yml.j2", "jinja2", id="26"),
        pytest.param("foo.j2.yaml", "jinja2", id="27"),
        pytest.param("foo.yaml.j2", "jinja2", id="28"),
        pytest.param(
            "examples/playbooks/rulebook.yml", "playbook", id="29"
        ),  # playbooks folder should determine kind
        pytest.param(
            "examples/rulebooks/rulebook-pass.yml", "rulebook", id="30"
        ),  # content should determine it as a rulebook
        pytest.param(
            "examples/yamllint/valid.yml", "yaml", id="31"
        ),  # empty yaml is valid yaml, not assuming anything else
        pytest.param(
            "examples/other/guess-1.yml", "playbook", id="32"
        ),  # content should determine is as a play
        pytest.param(
            "examples/playbooks/tasks/passing_task.yml", "tasks", id="33"
        ),  # content should determine is tasks
        pytest.param("examples/collection/galaxy.yml", "galaxy", id="34"),
        pytest.param("examples/meta/runtime.yml", "meta-runtime", id="35"),
        pytest.param("examples/meta/changelogs/changelog.yaml", "changelog", id="36"),
        pytest.param("examples/inventory/inventory.yml", "inventory", id="37"),
        pytest.param("examples/inventory/production.yml", "inventory", id="38"),
        pytest.param("examples/playbooks/vars/empty_vars.yml", "vars", id="39"),
        pytest.param(
            "examples/playbooks/vars/subfolder/settings.yaml", "vars", id="40"
        ),
        pytest.param(
            "examples/sanity_ignores/tests/sanity/ignore-2.14.txt",
            "sanity-ignore-file",
            id="41",
        ),
    ),
)
def test_kinds(monkeypatch: MonkeyPatch, path: str, kind: FileType) -> None:
    """Verify auto-detection logic based on DEFAULT_KINDS."""
    options = cli.get_config([])

    # pylint: disable=unused-argument
    def mockreturn(options: Namespace) -> dict[str, Any]:
        return {normpath(path): kind}

    # assert Lintable is able to determine file type
    lintable_detected = Lintable(path)
    lintable_expected = Lintable(path, kind=kind)
    assert lintable_detected == lintable_expected

    monkeypatch.setattr(file_utils, "discover_lintables", mockreturn)
    result = file_utils.discover_lintables(options)
    assert lintable_detected.kind == result[lintable_expected.name]


def test_guess_project_dir_tmp_path(tmp_path: Path) -> None:
    """Verify guess_project_dir()."""
    with cwd(str(tmp_path)):
        result = guess_project_dir(None)
        assert result == str(tmp_path)


def test_guess_project_dir_dotconfig() -> None:
    """Verify guess_project_dir()."""
    with cwd("examples"):
        assert os.path.exists(
            ".config/ansible-lint.yml"
        ), "Test requires config file inside .config folder."
        result = guess_project_dir(".config/ansible-lint.yml")
        assert result == str(os.getcwd())


BASIC_PLAYBOOK = """
- name: "playbook"
  tasks:
    - name: Hello
      debug:
        msg: 'world'
"""


@pytest.fixture(name="tmp_updated_lintable")
def fixture_tmp_updated_lintable(
    tmp_path: Path, path: str, content: str, updated_content: str
) -> Lintable:
    """Create a temp file Lintable with a content update that is not on disk."""
    lintable = Lintable(tmp_path / path, content)
    with lintable.path.open("w", encoding="utf-8") as f:
        f.write(content)
    # move mtime to a time in the past to avoid race conditions in the test
    mtime = time.time() - 60 * 60  # 1hr ago
    os.utime(str(lintable.path), (mtime, mtime))
    lintable.content = updated_content
    return lintable


@pytest.mark.parametrize(
    ("path", "content", "updated_content", "updated"),
    (
        pytest.param(
            "no_change.yaml", BASIC_PLAYBOOK, BASIC_PLAYBOOK, False, id="no_change"
        ),
        pytest.param(
            "quotes.yaml",
            BASIC_PLAYBOOK,
            BASIC_PLAYBOOK.replace('"', "'"),
            True,
            id="updated_quotes",
        ),
        pytest.param(
            "shorten.yaml", BASIC_PLAYBOOK, "# short file\n", True, id="shorten_file"
        ),
    ),
)
def test_lintable_updated(
    path: str, content: str, updated_content: str, updated: bool
) -> None:
    """Validate ``Lintable.updated`` when setting ``Lintable.content``."""
    lintable = Lintable(path, content)

    assert lintable.content == content

    lintable.content = updated_content

    assert lintable.content == updated_content

    assert lintable.updated is updated


@pytest.mark.parametrize(
    "updated_content", ((None,), (b"bytes",)), ids=("none", "bytes")
)
def test_lintable_content_setter_with_bad_types(updated_content: Any) -> None:
    """Validate ``Lintable.updated`` when setting ``Lintable.content``."""
    lintable = Lintable("bad_type.yaml", BASIC_PLAYBOOK)
    assert lintable.content == BASIC_PLAYBOOK

    with pytest.raises(TypeError):
        lintable.content = updated_content

    assert not lintable.updated


def test_lintable_with_new_file(tmp_path: Path) -> None:
    """Validate ``Lintable.updated`` for a new file."""
    lintable = Lintable(tmp_path / "new.yaml")

    lintable.content = BASIC_PLAYBOOK
    lintable.content = BASIC_PLAYBOOK
    assert lintable.content == BASIC_PLAYBOOK

    assert lintable.updated

    assert not lintable.path.exists()
    lintable.write()
    assert lintable.path.exists()
    assert lintable.path.read_text(encoding="utf-8") == BASIC_PLAYBOOK


@pytest.mark.parametrize(
    ("path", "force", "content", "updated_content", "updated"),
    (
        pytest.param(
            "no_change.yaml",
            False,
            BASIC_PLAYBOOK,
            BASIC_PLAYBOOK,
            False,
            id="no_change",
        ),
        pytest.param(
            "forced.yaml",
            True,
            BASIC_PLAYBOOK,
            BASIC_PLAYBOOK,
            False,
            id="forced_rewrite",
        ),
        pytest.param(
            "quotes.yaml",
            False,
            BASIC_PLAYBOOK,
            BASIC_PLAYBOOK.replace('"', "'"),
            True,
            id="updated_quotes",
        ),
        pytest.param(
            "shorten.yaml",
            False,
            BASIC_PLAYBOOK,
            "# short file\n",
            True,
            id="shorten_file",
        ),
        pytest.param(
            "forced.yaml",
            True,
            BASIC_PLAYBOOK,
            BASIC_PLAYBOOK.replace('"', "'"),
            True,
            id="forced_and_updated",
        ),
    ),
)
def test_lintable_write(
    tmp_updated_lintable: Lintable,
    force: bool,
    content: str,
    updated_content: str,
    updated: bool,
) -> None:
    """Validate ``Lintable.write`` writes when it should."""
    pre_updated = tmp_updated_lintable.updated
    pre_stat = tmp_updated_lintable.path.stat()

    tmp_updated_lintable.write(force=force)

    post_stat = tmp_updated_lintable.path.stat()
    post_updated = tmp_updated_lintable.updated

    # write() should not hide that an update happened
    assert pre_updated == post_updated == updated

    if force or updated:
        assert pre_stat.st_mtime < post_stat.st_mtime
    else:
        assert pre_stat.st_mtime == post_stat.st_mtime

    with tmp_updated_lintable.path.open("r", encoding="utf-8") as f:
        post_content = f.read()

    if updated:
        assert content != post_content
    else:
        assert content == post_content
    assert post_content == updated_content


@pytest.mark.parametrize(
    ("path", "content", "updated_content"),
    (
        pytest.param(
            "quotes.yaml",
            BASIC_PLAYBOOK,
            BASIC_PLAYBOOK.replace('"', "'"),
            id="updated_quotes",
        ),
    ),
)
def test_lintable_content_deleter(
    tmp_updated_lintable: Lintable,
    content: str,
    updated_content: str,
) -> None:
    """Ensure that resetting content cache triggers re-reading file."""
    assert content != updated_content
    assert tmp_updated_lintable.content == updated_content
    del tmp_updated_lintable.content
    assert tmp_updated_lintable.content == content


@pytest.mark.parametrize(
    ("path", "result"),
    (
        pytest.param("foo", "foo", id="rel"),
        pytest.param(os.path.expanduser("~/xxx"), "~/xxx", id="rel-to-home"),
        pytest.param("/a/b/c", "/a/b/c", id="absolute"),
        pytest.param(
            "examples/playbooks/roles", "examples/roles", id="resolve-symlink"
        ),
    ),
)
def test_normpath_path(path: str, result: str) -> None:
    """Tests behavior of normpath."""
    assert normpath_path(path) == Path(result)


def test_bug_2513(
    tmp_path: Path,
    default_rules_collection: RulesCollection,
) -> None:
    """Regression test for bug 2513.

    Test that when CWD is outside ~, and argument is like ~/playbook.yml
    we will still be able to process the files.
    See: https://github.com/ansible/ansible-lint/issues/2513
    """
    filename = "~/.cache/ansible-lint/playbook.yml"
    os.makedirs(os.path.dirname(os.path.expanduser(filename)), exist_ok=True)
    lintable = Lintable(filename, content="---\n- hosts: all\n")
    lintable.write(force=True)
    with cwd(str(tmp_path)):
        results = Runner(filename, rules=default_rules_collection).run()
        assert len(results) == 1
        assert results[0].rule.id == "name"
