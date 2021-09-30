# -*- coding: utf-8 -*-

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
"""Tests for generic utilitary functions."""

import logging
import os
import os.path
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple, Union

import pytest
from _pytest.capture import CaptureFixture
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from ansiblelint import cli, constants, file_utils, utils
from ansiblelint.__main__ import initialize_logger
from ansiblelint.cli import get_rules_dirs
from ansiblelint.constants import FileType
from ansiblelint.file_utils import (
    Lintable,
    expand_path_vars,
    expand_paths_vars,
    guess_project_dir,
    normpath,
)
from ansiblelint.testing import run_ansible_lint

from .conftest import cwd


@pytest.mark.parametrize(
    ('string', 'expected_cmd', 'expected_args', 'expected_kwargs'),
    (
        pytest.param('', '', [], {}, id='blank'),
        pytest.param('vars:', 'vars', [], {}, id='single_word'),
        pytest.param('hello: a=1', 'hello', [], {'a': '1'}, id='string_module_and_arg'),
        pytest.param('action: hello a=1', 'hello', [], {'a': '1'}, id='strips_action'),
        pytest.param(
            'action: whatever bobbins x=y z=x c=3',
            'whatever',
            ['bobbins', 'x=y', 'z=x', 'c=3'],
            {},
            id='more_than_one_arg',
        ),
        pytest.param(
            'action: command chdir=wxy creates=zyx tar xzf zyx.tgz',
            'command',
            ['tar', 'xzf', 'zyx.tgz'],
            {'chdir': 'wxy', 'creates': 'zyx'},
            id='command_with_args',
        ),
    ),
)
def test_tokenize(
    string: str,
    expected_cmd: str,
    expected_args: Sequence[str],
    expected_kwargs: Dict[str, Any],
) -> None:
    """Test that tokenize works for different input types."""
    (cmd, args, kwargs) = utils.tokenize(string)
    assert cmd == expected_cmd
    assert args == expected_args
    assert kwargs == expected_kwargs


@pytest.mark.parametrize(
    ('reference_form', 'alternate_forms'),
    (
        pytest.param(
            dict(name='hello', action='command chdir=abc echo hello world'),
            (dict(name="hello", command="chdir=abc echo hello world"),),
            id='simple_command',
        ),
        pytest.param(
            {'git': {'version': 'abc'}, 'args': {'repo': 'blah', 'dest': 'xyz'}},
            (
                {'git': {'version': 'abc', 'repo': 'blah', 'dest': 'xyz'}},
                {"git": 'version=abc repo=blah dest=xyz'},
                {
                    "git": None,
                    "args": {'repo': 'blah', 'dest': 'xyz', 'version': 'abc'},
                },
            ),
            id='args',
        ),
    ),
)
def test_normalize(
    reference_form: Dict[str, Any], alternate_forms: Tuple[Dict[str, Any]]
) -> None:
    """Test that tasks specified differently are normalized same way."""
    normal_form = utils.normalize_task(reference_form, 'tasks.yml')

    for form in alternate_forms:
        assert normal_form == utils.normalize_task(form, 'tasks.yml')


def test_normalize_complex_command() -> None:
    """Test that tasks specified differently are normalized same way."""
    task1 = dict(
        name="hello", action={'module': 'pip', 'name': 'df', 'editable': 'false'}
    )
    task2 = dict(name="hello", pip={'name': 'df', 'editable': 'false'})
    task3 = dict(name="hello", pip="name=df editable=false")
    task4 = dict(name="hello", action="pip name=df editable=false")
    assert utils.normalize_task(task1, 'tasks.yml') == utils.normalize_task(
        task2, 'tasks.yml'
    )
    assert utils.normalize_task(task2, 'tasks.yml') == utils.normalize_task(
        task3, 'tasks.yml'
    )
    assert utils.normalize_task(task3, 'tasks.yml') == utils.normalize_task(
        task4, 'tasks.yml'
    )


def test_extract_from_list() -> None:
    """Check that tasks get extracted from blocks if present."""
    block = {
        'block': [{'tasks': {'name': 'hello', 'command': 'whoami'}}],
        'test_none': None,
        'test_string': 'foo',
    }
    blocks = [block]

    test_list = utils.extract_from_list(blocks, ['block'])
    test_none = utils.extract_from_list(blocks, ['test_none'])

    assert list(block['block']) == test_list  # type: ignore
    assert list() == test_none
    with pytest.raises(RuntimeError):
        utils.extract_from_list(blocks, ['test_string'])


@pytest.mark.parametrize(
    ('template', 'output'),
    (
        pytest.param('{{ playbook_dir }}', '/a/b/c', id='simple'),
        pytest.param(
            "{{ 'hello' | doesnotexist }}",
            "{{ 'hello' | doesnotexist }}",
            id='unknown_filter',
        ),
        pytest.param(
            '{{ hello | to_json }}',
            '{{ hello | to_json }}',
            id='to_json_filter_on_undefined_variable',
        ),
        pytest.param(
            '{{ hello | to_nice_yaml }}',
            '{{ hello | to_nice_yaml }}',
            id='to_nice_yaml_filter_on_undefined_variable',
        ),
    ),
)
def test_template(template: str, output: str) -> None:
    """Verify that resolvable template vars and filters get rendered."""
    result = utils.template('/base/dir', template, dict(playbook_dir='/a/b/c'))
    assert result == output


@pytest.mark.parametrize(
    ("role", "expect_warning"),
    (
        ("template_lookup", False),
        ("template_lookup_missing", True),
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
    assert ("Unable to find" in result.stderr) == expect_warning


def test_task_to_str_unicode() -> None:
    """Ensure that extracting messages from tasks preserves Unicode."""
    task = dict(fail=dict(msg=u"unicode é ô à"))
    result = utils.task_to_str(utils.normalize_task(task, 'filename.yml'))
    assert result == u"fail msg=unicode é ô à"


@pytest.mark.parametrize(
    'path',
    (
        pytest.param(Path('a/b/../'), id='pathlib.Path'),
        pytest.param('a/b/../', id='str'),
    ),
)
def test_normpath_with_path_object(path: str) -> None:
    """Ensure that relative parent dirs are normalized in paths."""
    assert normpath(path) == "a"


def test_expand_path_vars(monkeypatch: MonkeyPatch) -> None:
    """Ensure that tilde and env vars are expanded in paths."""
    test_path = '/test/path'
    monkeypatch.setenv('TEST_PATH', test_path)
    assert expand_path_vars('~') == os.path.expanduser('~')
    assert expand_path_vars('$TEST_PATH') == test_path


@pytest.mark.parametrize(
    ('test_path', 'expected'),
    (
        pytest.param(Path('$TEST_PATH'), "/test/path", id='pathlib.Path'),
        pytest.param('$TEST_PATH', "/test/path", id='str'),
        pytest.param('  $TEST_PATH  ', "/test/path", id='stripped-str'),
        pytest.param('~', os.path.expanduser('~'), id='home'),
    ),
)
def test_expand_paths_vars(
    test_path: Union[str, Path], expected: str, monkeypatch: MonkeyPatch
) -> None:
    """Ensure that tilde and env vars are expanded in paths lists."""
    monkeypatch.setenv('TEST_PATH', '/test/path')
    assert expand_paths_vars([test_path]) == [expected]  # type: ignore


@pytest.mark.parametrize(
    ('reset_env_var', 'message_prefix'),
    (
        # simulate absence of git command
        ('PATH', "Failed to locate command: "),
        # simulate a missing git repo
        ('GIT_DIR', "Looking up for files"),
    ),
    ids=('no-git-cli', 'outside-git-repo'),
)
def test_discover_lintables_git_verbose(
    reset_env_var: str,
    message_prefix: str,
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
) -> None:
    """Ensure that autodiscovery lookup failures are logged."""
    options = cli.get_config(['-v'])
    initialize_logger(options.verbosity)
    monkeypatch.setenv(reset_env_var, '')
    file_utils.discover_lintables(options)

    assert any(m[2].startswith("Looking up for files") for m in caplog.record_tuples)
    assert any(m.startswith(message_prefix) for m in caplog.messages)


@pytest.mark.parametrize(
    'is_in_git',
    (True, False),
    ids=('in Git', 'outside Git'),
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
    lint_path = test_dir / '..' / 'examples' / 'roles' / 'test-role'
    if not is_in_git:
        monkeypatch.setenv('GIT_DIR', '')

    yaml_count = len(list(lint_path.glob('**/*.yml'))) + len(
        list(lint_path.glob('**/*.yaml'))
    )

    monkeypatch.chdir(str(lint_path))
    files = file_utils.discover_lintables(options)
    stderr = capsys.readouterr().err
    assert not stderr, 'No stderr output is expected when the verbosity is off'
    assert (
        len(files) == yaml_count
    ), "Expected to find {yaml_count} yaml files in {lint_path}".format_map(
        locals(),
    )


def test_discover_lintables_umlaut(monkeypatch: MonkeyPatch) -> None:
    """Verify that filenames containing German umlauts are not garbled by the discover_lintables."""
    options = cli.get_config([])
    test_dir = Path(__file__).resolve().parent
    lint_path = test_dir / '..' / 'examples' / 'playbooks'

    monkeypatch.chdir(str(lint_path))
    files = file_utils.discover_lintables(options)
    assert '"with-umlaut-\\303\\244.yml"' not in files
    assert 'with-umlaut-ä.yml' in files


def test_logger_debug(caplog: LogCaptureFixture) -> None:
    """Test that the double verbosity arg causes logger to be DEBUG."""
    options = cli.get_config(['-vv'])
    initialize_logger(options.verbosity)

    expected_info = (
        "ansiblelint.__main__",
        logging.DEBUG,
        'Logging initialized to level 10',
    )

    assert expected_info in caplog.record_tuples


def test_cli_auto_detect(capfd: CaptureFixture[str]) -> None:
    """Test that run without arguments it will detect and lint the entire repository."""
    cmd = [
        sys.executable,
        "-m",
        "ansiblelint",
        "-v",
        "-p",
        "--nocolor",
    ]
    result = subprocess.run(cmd, check=False).returncode

    # We de expect to fail on our own repo due to test examples we have
    # TODO(ssbarnea) replace it with exact return code once we document them
    assert result != 0

    out, err = capfd.readouterr()

    # Confirmation that it runs in auto-detect mode
    assert (
        "Discovered files to lint using: git ls-files --cached --others --exclude-standard -z"
        in err
    )
    assert "Excluded removed files using: git ls-files --deleted -z" in err
    # An expected rule match from our examples
    assert (
        "examples/playbooks/empty_playbook.yml:1: "
        "syntax-check Empty playbook, nothing to do" in out
    )
    # assures that our .ansible-lint exclude was effective in excluding github files
    assert "Identified: .github/" not in out
    # assures that we can parse playbooks as playbooks
    assert "Identified: test/test/always-run-success.yml" not in err
    # assure that zuul_return missing module is not reported
    assert "examples/playbooks/mocked_dependency.yml" not in out
    assert "Executing syntax check on examples/playbooks/mocked_dependency.yml" in err


def test_is_playbook() -> None:
    """Verify that we can detect a playbook as a playbook."""
    assert utils.is_playbook("examples/playbooks/always-run-success.yml")


@pytest.mark.parametrize(
    ('path', 'kind'),
    (
        ("foo/playbook.yml", "playbook"),
        ("playbooks/foo.yml", "playbook"),
        ("playbooks/roles/foo.yml", "yaml"),
        # the only yml file that is not a playbook inside molecule/ folders
        (".config/molecule/config.yml", "yaml"),  # molecule shared config
        ("roles/foo/molecule/scen1/base.yml", "yaml"),  # molecule scenario base config
        ("roles/foo/molecule/scen1/molecule.yml", "yaml"),  # molecule scenario config
        ("roles/foo/molecule/scen2/foobar.yml", "playbook"),  # custom playbook name
        ("roles/foo/molecule/scen3/converge.yml", "playbook"),  # common playbook name
        ("roles/foo/molecule/scen3/requirements.yml", "requirements"),  # requirements
        ("roles/foo/molecule/scen3/collections.yml", "requirements"),  # requirements
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

    monkeypatch.setattr(file_utils, 'discover_lintables', mockreturn)
    result = file_utils.discover_lintables(options)
    # get_lintable could return additional files and we only care to see
    # that the given file is among the returned list.
    assert lintable_detected.name in result
    assert lintable_detected.kind == result[lintable_expected.name]


def test_auto_detect_exclude(monkeypatch: MonkeyPatch) -> None:
    """Verify that exclude option can be used to narrow down detection."""
    options = cli.get_config(['--exclude', 'foo'])

    def mockreturn(options: Namespace) -> List[str]:
        return ['foo/playbook.yml', 'bar/playbook.yml']

    monkeypatch.setattr(utils, 'discover_lintables', mockreturn)
    result = utils.get_lintables(options)
    assert result == [Lintable('bar/playbook.yml', kind='playbook')]


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
    user_ruledirs: List[str], use_default: bool, expected: List[str]
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
    user_ruledirs: List[str],
    use_default: bool,
    expected: List[str],
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
    assert list(utils.nested_items(data)) == items


def test_guess_project_dir(tmp_path: Path) -> None:
    """Verify guess_project_dir()."""
    with cwd(str(tmp_path)):
        result = guess_project_dir(None)
        assert result == str(tmp_path)
