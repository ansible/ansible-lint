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
"""Tests for generic utility functions."""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from ansible.utils.sentinel import Sentinel
from ansible_compat.runtime import Runtime

from ansiblelint import cli, constants, utils
from ansiblelint.__main__ import initialize_logger
from ansiblelint.cli import get_rules_dirs
from ansiblelint.constants import RC
from ansiblelint.file_utils import Lintable, cwd
from ansiblelint.runner import Runner

if TYPE_CHECKING:
    from collections.abc import Sequence

    from _pytest.capture import CaptureFixture
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch

    from ansiblelint.rules import RulesCollection


runtime = Runtime(require_module=True)


@pytest.mark.parametrize(
    ("string", "expected_args", "expected_kwargs"),
    (
        pytest.param("", [], {}, id="a"),
        pytest.param("a=1", [], {"a": "1"}, id="b"),
        pytest.param("hello a=1", ["hello"], {"a": "1"}, id="c"),
        pytest.param(
            "whatever bobbins x=y z=x c=3",
            ["whatever", "bobbins"],
            {"x": "y", "z": "x", "c": "3"},
            id="more_than_one_arg",
        ),
        pytest.param(
            "command chdir=wxy creates=zyx tar xzf zyx.tgz",
            ["command", "tar", "xzf", "zyx.tgz"],
            {"chdir": "wxy", "creates": "zyx"},
            id="command_with_args",
        ),
        pytest.param(
            "{{ varset }}.yml",
            ["{{ varset }}.yml"],
            {},
            id="x",
        ),
        pytest.param(
            "foo bar.yml",
            ["foo bar.yml"],
            {},
            id="path-with-spaces",
        ),
    ),
)
def test_tokenize(
    string: str,
    expected_args: Sequence[str],
    expected_kwargs: dict[str, Any],
) -> None:
    """Test that tokenize works for different input types."""
    (args, kwargs) = utils.tokenize(string)
    assert args == expected_args
    assert kwargs == expected_kwargs


@pytest.mark.parametrize(
    ("reference_form", "alternate_forms"),
    (
        pytest.param(
            {"name": "hello", "action": "command chdir=abc echo hello world"},
            ({"name": "hello", "command": "chdir=abc echo hello world"},),
            id="simple_command",
        ),
        pytest.param(
            {"git": {"version": "abc"}, "args": {"repo": "blah", "dest": "xyz"}},
            (
                {"git": {"version": "abc", "repo": "blah", "dest": "xyz"}},
                {"git": "version=abc repo=blah dest=xyz"},
                {
                    "git": None,
                    "args": {"repo": "blah", "dest": "xyz", "version": "abc"},
                },
            ),
            id="args",
        ),
    ),
)
def test_normalize(
    reference_form: dict[str, Any],
    alternate_forms: tuple[dict[str, Any]],
) -> None:
    """Test that tasks specified differently are normalized same way."""
    task = utils.Task(reference_form, filename="tasks.yml")
    normal_form = task._normalize_task()  # noqa: SLF001

    for form in alternate_forms:
        task2 = utils.Task(form, filename="tasks.yml")
        assert normal_form == task2._normalize_task()  # noqa: SLF001


def test_normalize_complex_command() -> None:
    """Test that tasks specified differently are normalized same way."""
    task1 = utils.Task(
        {
            "name": "hello",
            "action": {"module": "pip", "name": "df", "editable": "false"},
        },
        filename="tasks.yml",
    )
    task2 = utils.Task(
        {"name": "hello", "pip": {"name": "df", "editable": "false"}},
        filename="tasks.yml",
    )
    task3 = utils.Task(
        {"name": "hello", "pip": "name=df editable=false"},
        filename="tasks.yml",
    )
    task4 = utils.Task(
        {"name": "hello", "action": "pip name=df editable=false"},
        filename="tasks.yml",
    )
    assert task1._normalize_task() == task2._normalize_task()  # noqa: SLF001
    assert task2._normalize_task() == task3._normalize_task()  # noqa: SLF001
    assert task3._normalize_task() == task4._normalize_task()  # noqa: SLF001


@pytest.mark.parametrize(
    ("task_raw", "expected_form"),
    (
        pytest.param(
            {
                "name": "ensure apache is at the latest version",
                "yum": {"name": "httpd", "state": "latest"},
            },
            {
                "delegate_to": Sentinel,
                "name": "ensure apache is at the latest version",
                "action": {
                    "__ansible_module__": "yum",
                    "__ansible_module_original__": "yum",
                    "name": "httpd",
                    "state": "latest",
                },
            },
            id="0",
        ),
        pytest.param(
            {
                "name": "Attempt and graceful roll back",
                "block": [
                    {
                        "name": "Install httpd and memcached",
                        "ansible.builtin.yum": ["httpd", "memcached"],
                        "state": "present",
                    },
                ],
            },
            {
                "name": "Attempt and graceful roll back",
                "block": [
                    {
                        "name": "Install httpd and memcached",
                        "ansible.builtin.yum": ["httpd", "memcached"],
                        "state": "present",
                    },
                ],
                "action": {
                    "__ansible_module__": "block/always/rescue",
                    "__ansible_module_original__": "block/always/rescue",
                },
            },
            id="1",
        ),
    ),
)
def test_normalize_task_v2(
    task_raw: dict[str, Any],
    expected_form: dict[str, Any],
) -> None:
    """Check that it normalizes task and returns the expected form."""
    task = utils.Task(task_raw)
    assert utils.normalize_task_v2(task) == expected_form


def test_extract_from_list() -> None:
    """Check that tasks get extracted from blocks if present."""
    block = {
        "block": [{"tasks": {"name": "hello", "command": "whoami"}}],
        "test_none": None,
        "test_string": "foo",
    }
    blocks = [block]

    test_list = utils.extract_from_list(blocks, ["block"])
    test_none = utils.extract_from_list(blocks, ["test_none"])

    assert list(block["block"]) == test_list  # type: ignore[arg-type]
    assert not test_none
    with pytest.raises(RuntimeError):
        utils.extract_from_list(blocks, ["test_string"])


def test_extract_from_list_recursive() -> None:
    """Check that tasks get extracted from blocks if present."""
    block = {
        "block": [{"block": [{"name": "hello", "command": "whoami"}]}],
    }
    blocks = [block]

    test_list = utils.extract_from_list(blocks, ["block"])
    assert list(block["block"]) == test_list

    test_list_recursive = utils.extract_from_list(blocks, ["block"], recursive=True)
    assert block["block"] + block["block"][0]["block"] == test_list_recursive


@pytest.mark.parametrize(
    ("template", "output"),
    (
        pytest.param("{{ playbook_dir }}", "/a/b/c", id="simple"),
        pytest.param(
            "{{ 'hello' | doesnotexist }}",
            "hello",  # newer implementation ignores unknown filters
            id="unknown_filter",
        ),
        pytest.param(
            "{{ hello | to_json }}",
            "{{ hello | to_json }}",
            id="to_json_filter_on_undefined_variable",
        ),
        pytest.param(
            "{{ hello | to_nice_yaml }}",
            "{{ hello | to_nice_yaml }}",
            id="to_nice_yaml_filter_on_undefined_variable",
        ),
    ),
)
def test_template(template: str, output: str) -> None:
    """Verify that resolvable template vars and filters get rendered."""
    result = utils.template(
        basedir=Path("/base/dir"),
        value=template,
        variables={"playbook_dir": "/a/b/c"},
        fail_on_error=False,
    )
    assert result == output


def test_task_to_str_unicode() -> None:
    """Ensure that extracting messages from tasks preserves Unicode."""
    task = utils.Task({"fail": {"msg": "unicode é ô à"}}, filename="filename.yml")
    result = utils.task_to_str(task._normalize_task())  # noqa: SLF001
    assert result == "fail msg=unicode é ô à"


def test_logger_debug(caplog: LogCaptureFixture) -> None:
    """Test that the double verbosity arg causes logger to be DEBUG."""
    options = cli.get_config(["-vv"])
    initialize_logger(options.verbosity)

    expected_info = (
        "ansiblelint.__main__",
        logging.DEBUG,
        "Logging initialized to level 10",
    )

    assert expected_info in caplog.record_tuples


def test_cli_auto_detect(capfd: CaptureFixture[str]) -> None:
    """Test that run without arguments it will detect and lint the entire repository."""
    cmd = [
        sys.executable,
        "-m",
        "ansiblelint",
        "-x",
        "schema",  # exclude schema as our test file would fail it
        "-v",
        "-p",
        "--nocolor",
    ]
    result = subprocess.run(cmd, check=False).returncode

    # We de expect to fail on our own repo due to test examples we have
    assert result == RC.VIOLATIONS_FOUND

    out, err = capfd.readouterr()

    # An expected rule match from our examples
    assert (
        "examples/playbooks/empty_playbook.yml:1:1: "
        "syntax-check[empty-playbook]: Empty playbook, nothing to do" in out
    )
    # assures that our ansible-lint config exclude was effective in excluding github files
    assert "Identified: .github/" not in out
    # assures that we can parse playbooks as playbooks
    assert "Identified: test/test/always-run-success.yml" not in err
    assert (
        "Executing syntax check on playbook examples/playbooks/mocked_dependency.yml"
        in err
    )


def test_is_playbook() -> None:
    """Verify that we can detect a playbook as a playbook."""
    assert utils.is_playbook("examples/playbooks/always-run-success.yml")


@pytest.mark.parametrize(
    "exclude",
    (pytest.param("foo", id="1"), pytest.param("foo/", id="2")),
)
def test_auto_detect_exclude(tmp_path: Path, exclude: str) -> None:
    """Verify that exclude option can be used to narrow down detection."""
    with cwd(tmp_path):
        subprocess.check_output(
            "git init",
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            cwd=tmp_path,
        )
        (tmp_path / "foo").mkdir()
        (tmp_path / "bar").mkdir()
        (tmp_path / "foo" / "playbook.yml").touch()
        (tmp_path / "bar" / "playbook.yml").touch()

        options = cli.get_config(["--exclude", exclude])
        options.cwd = tmp_path
        result = utils.get_lintables(options)
        assert result == [Lintable("bar/playbook.yml", kind="playbook")]

        # now we also test with .gitignore exclude approach
        (tmp_path / ".gitignore").write_text(f".gitignore\n{exclude}\n")
        options = cli.get_config([])
        options.cwd = tmp_path
        result = utils.get_lintables(options)
        assert result == [Lintable("bar/playbook.yml", kind="playbook")]


_DEFAULT_RULEDIRS = [constants.DEFAULT_RULESDIR]
_CUSTOM_RULESDIR = Path(__file__).parent / "custom_rules"
_CUSTOM_RULEDIRS = [
    _CUSTOM_RULESDIR / "example_inc",
    _CUSTOM_RULESDIR / "example_com",
]


@pytest.mark.parametrize(
    ("user_ruledirs", "use_default", "expected"),
    (
        ([], True, _DEFAULT_RULEDIRS),
        ([], False, _DEFAULT_RULEDIRS),
        (_CUSTOM_RULEDIRS, True, _CUSTOM_RULEDIRS + _DEFAULT_RULEDIRS),
        (_CUSTOM_RULEDIRS, False, _CUSTOM_RULEDIRS),
    ),
)
def test_get_rules_dirs(
    user_ruledirs: list[Path],
    use_default: bool,
    expected: list[Path],
) -> None:
    """Test it returns expected dir lists."""
    assert get_rules_dirs(user_ruledirs, use_default=use_default) == expected


@pytest.mark.parametrize(
    ("user_ruledirs", "use_default", "expected"),
    (
        ([], True, sorted(_CUSTOM_RULEDIRS) + _DEFAULT_RULEDIRS),
        ([], False, sorted(_CUSTOM_RULEDIRS) + _DEFAULT_RULEDIRS),
        (
            _CUSTOM_RULEDIRS,
            True,
            _CUSTOM_RULEDIRS + sorted(_CUSTOM_RULEDIRS) + _DEFAULT_RULEDIRS,
        ),
        (_CUSTOM_RULEDIRS, False, _CUSTOM_RULEDIRS),
    ),
)
def test_get_rules_dirs_with_custom_rules(
    user_ruledirs: list[Path],
    use_default: bool,
    expected: list[Path],
    monkeypatch: MonkeyPatch,
) -> None:
    """Test it returns expected dir lists when custom rules exist."""
    monkeypatch.setenv(constants.CUSTOM_RULESDIR_ENVVAR, str(_CUSTOM_RULESDIR))
    assert get_rules_dirs(user_ruledirs, use_default=use_default) == expected


def test_find_children(default_rules_collection: RulesCollection) -> None:
    """Verify correct function of find_children()."""
    Runner(
        rules=default_rules_collection,
    ).find_children(Lintable("examples/playbooks/find_children.yml"))


def test_find_children_in_task(default_rules_collection: RulesCollection) -> None:
    """Verify correct function of find_children() in tasks."""
    Runner(
        Lintable("examples/playbooks/tasks/bug-2875.yml"),
        rules=default_rules_collection,
    ).run()


@pytest.mark.parametrize(
    ("file", "names", "positions"),
    (
        pytest.param(
            "examples/playbooks/task_in_list-0.yml",
            ["A", "B", "C", "D", "E", "F", "G"],
            [
                ".[0].tasks[0]",
                ".[0].tasks[1]",
                ".[0].pre_tasks[0]",
                ".[0].post_tasks[0]",
                ".[0].post_tasks[0].block[0]",
                ".[0].post_tasks[0].rescue[0]",
                ".[0].post_tasks[0].always[0]",
            ],
            id="0",
        ),
    ),
)
def test_task_in_list(file: str, names: list[str], positions: list[str]) -> None:
    """Check that tasks get extracted from blocks if present."""
    lintable = Lintable(file)
    assert lintable.kind
    tasks = list(
        utils.task_in_list(data=lintable.data, file=lintable, kind=lintable.kind),
    )
    assert len(tasks) == len(names)
    for index, task in enumerate(tasks):
        assert task.name == names[index]
        assert task.position == positions[index]


def test_find_children_in_module(default_rules_collection: RulesCollection) -> None:
    """Verify correct function of find_children() in tasks."""
    lintable = Lintable("plugins/modules/fake_module.py")
    children = Runner(
        rules=default_rules_collection,
    ).find_children(lintable)
    assert len(children) == 1
    child = children[0]

    # Parent is a python file
    assert lintable.base_kind == "text/python"

    # Child correctly looks like a YAML file
    assert child.base_kind == "text/yaml"
    assert child.content.startswith("---")
