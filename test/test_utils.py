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
import os
import os.path
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Sequence

import pytest
from _pytest.capture import CaptureFixture
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from ansible.utils.sentinel import Sentinel
from ansible_compat.runtime import Runtime

from ansiblelint import cli, constants, utils
from ansiblelint.__main__ import initialize_logger
from ansiblelint.cli import get_rules_dirs
from ansiblelint.constants import VIOLATIONS_FOUND_RC
from ansiblelint.file_utils import Lintable
from ansiblelint.testing import run_ansible_lint

runtime = Runtime()


@pytest.mark.parametrize(
    ("string", "expected_cmd", "expected_args", "expected_kwargs"),
    (
        pytest.param("", "", [], {}, id="blank"),
        pytest.param("vars:", "vars", [], {}, id="single_word"),
        pytest.param("hello: a=1", "hello", [], {"a": "1"}, id="string_module_and_arg"),
        pytest.param("action: hello a=1", "hello", [], {"a": "1"}, id="strips_action"),
        pytest.param(
            "action: whatever bobbins x=y z=x c=3",
            "whatever",
            ["bobbins", "x=y", "z=x", "c=3"],
            {},
            id="more_than_one_arg",
        ),
        pytest.param(
            "action: command chdir=wxy creates=zyx tar xzf zyx.tgz",
            "command",
            ["tar", "xzf", "zyx.tgz"],
            {"chdir": "wxy", "creates": "zyx"},
            id="command_with_args",
        ),
    ),
)
def test_tokenize(
    string: str,
    expected_cmd: str,
    expected_args: Sequence[str],
    expected_kwargs: dict[str, Any],
) -> None:
    """Test that tokenize works for different input types."""
    (cmd, args, kwargs) = utils.tokenize(string)
    assert cmd == expected_cmd
    assert args == expected_args
    assert kwargs == expected_kwargs


@pytest.mark.parametrize(
    ("reference_form", "alternate_forms"),
    (
        pytest.param(
            dict(name="hello", action="command chdir=abc echo hello world"),
            (dict(name="hello", command="chdir=abc echo hello world"),),
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
    reference_form: dict[str, Any], alternate_forms: tuple[dict[str, Any]]
) -> None:
    """Test that tasks specified differently are normalized same way."""
    normal_form = utils.normalize_task(reference_form, "tasks.yml")

    for form in alternate_forms:
        assert normal_form == utils.normalize_task(form, "tasks.yml")


def test_normalize_complex_command() -> None:
    """Test that tasks specified differently are normalized same way."""
    task1 = dict(
        name="hello", action={"module": "pip", "name": "df", "editable": "false"}
    )
    task2 = dict(name="hello", pip={"name": "df", "editable": "false"})
    task3 = dict(name="hello", pip="name=df editable=false")
    task4 = dict(name="hello", action="pip name=df editable=false")
    assert utils.normalize_task(task1, "tasks.yml") == utils.normalize_task(
        task2, "tasks.yml"
    )
    assert utils.normalize_task(task2, "tasks.yml") == utils.normalize_task(
        task3, "tasks.yml"
    )
    assert utils.normalize_task(task3, "tasks.yml") == utils.normalize_task(
        task4, "tasks.yml"
    )


@pytest.mark.parametrize(
    ("task", "expected_form"),
    (
        pytest.param(
            dict(
                name="ensure apache is at the latest version",
                yum={"name": "httpd", "state": "latest"},
            ),
            dict(
                delegate_to=Sentinel,
                name="ensure apache is at the latest version",
                action={
                    "__ansible_module__": "yum",
                    "__ansible_module_original__": "yum",
                    "__ansible_arguments__": [],
                    "name": "httpd",
                    "state": "latest",
                },
            ),
        ),
        pytest.param(
            dict(
                name="Attempt and graceful roll back",
                block=[
                    {
                        "name": "Install httpd and memcached",
                        "ansible.builtin.yum": ["httpd", "memcached"],
                        "state": "present",
                    }
                ],
            ),
            dict(
                name="Attempt and graceful roll back",
                block=[
                    {
                        "name": "Install httpd and memcached",
                        "ansible.builtin.yum": ["httpd", "memcached"],
                        "state": "present",
                    }
                ],
                action={
                    "__ansible_module__": "block/always/rescue",
                    "__ansible_module_original__": "block/always/rescue",
                },
            ),
        ),
    ),
)
def test_normalize_task_v2(task: dict[str, Any], expected_form: dict[str, Any]) -> None:
    """Check that it normalizes task and returns the expected form."""
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

    assert list(block["block"]) == test_list  # type: ignore
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
        basedir="/base/dir",
        value=template,
        variables=dict(playbook_dir="/a/b/c"),
        fail_on_error=False,
    )
    assert result == output


@pytest.mark.parametrize(
    ("role", "expect_warning"),
    (
        ("template_lookup", False),
        # With 2.15 ansible replaced the runtime Warning about inability to
        # open a file in file lookup with a full error.
        ("template_lookup_missing", runtime.version_in_range(upper="2.15.0.dev0")),
    ),
)
def test_template_lookup(role: str, expect_warning: bool) -> None:
    """Assure lookup plugins used in templates does not trigger Ansible warnings."""
    task_path = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..",
            "examples",
            "roles",
            role,
            "tasks",
            "main.yml",
        )
    )
    result = run_ansible_lint("-v", task_path)
    # 2.13 or older will not attempt to install when in offline mode
    if not runtime.version_in_range(upper="2.14.0.dev0"):
        assert ("Unable to find" in result.stderr) == expect_warning


def test_task_to_str_unicode() -> None:
    """Ensure that extracting messages from tasks preserves Unicode."""
    task = dict(fail=dict(msg="unicode é ô à"))
    result = utils.task_to_str(utils.normalize_task(task, "filename.yml"))
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
    assert result == VIOLATIONS_FOUND_RC

    out, err = capfd.readouterr()

    # Confirmation that it runs in auto-detect mode
    assert (
        "Discovered files to lint using: git ls-files --cached --others --exclude-standard -z"
        in err
    )
    assert "Excluded removed files using: git ls-files --deleted -z" in err
    # An expected rule match from our examples
    assert (
        "examples/playbooks/empty_playbook.yml:1:1: "
        "warning[empty-playbook]: Empty playbook, nothing to do" in out
    )
    # assures that our ansible-lint config exclude was effective in excluding github files
    assert "Identified: .github/" not in out
    # assures that we can parse playbooks as playbooks
    assert "Identified: test/test/always-run-success.yml" not in err
    assert "Executing syntax check on examples/playbooks/mocked_dependency.yml" in err


def test_is_playbook() -> None:
    """Verify that we can detect a playbook as a playbook."""
    assert utils.is_playbook("examples/playbooks/always-run-success.yml")


def test_auto_detect_exclude(monkeypatch: MonkeyPatch) -> None:
    """Verify that exclude option can be used to narrow down detection."""
    options = cli.get_config(["--exclude", "foo"])

    # pylint: disable=unused-argument
    def mockreturn(options: Namespace) -> list[str]:
        return ["foo/playbook.yml", "bar/playbook.yml"]

    monkeypatch.setattr(utils, "discover_lintables", mockreturn)
    result = utils.get_lintables(options)
    assert result == [Lintable("bar/playbook.yml", kind="playbook")]


_DEFAULT_RULEDIRS = [constants.DEFAULT_RULESDIR]
_CUSTOM_RULESDIR = Path(__file__).parent / "custom_rules"
_CUSTOM_RULEDIRS = [
    str(_CUSTOM_RULESDIR / "example_inc"),
    str(_CUSTOM_RULESDIR / "example_com"),
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
    user_ruledirs: list[str], use_default: bool, expected: list[str]
) -> None:
    """Test it returns expected dir lists."""
    assert get_rules_dirs(user_ruledirs, use_default) == expected


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
    user_ruledirs: list[str],
    use_default: bool,
    expected: list[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Test it returns expected dir lists when custom rules exist."""
    monkeypatch.setenv(constants.CUSTOM_RULESDIR_ENVVAR, str(_CUSTOM_RULESDIR))
    assert get_rules_dirs(user_ruledirs, use_default) == expected


def test_nested_items() -> None:
    """Verify correct function of nested_items()."""
    data = {"foo": "text", "bar": {"some": "text2"}, "fruits": ["apple", "orange"]}

    items = [
        ("foo", "text", ""),
        ("bar", {"some": "text2"}, ""),
        ("some", "text2", "bar"),
        ("fruits", ["apple", "orange"], ""),
        ("list-item", "apple", "fruits"),
        ("list-item", "orange", "fruits"),
    ]
    with pytest.deprecated_call(
        match=r"Call to deprecated function ansiblelint\.utils\.nested_items.*"
    ):
        assert list(utils.nested_items(data)) == items
