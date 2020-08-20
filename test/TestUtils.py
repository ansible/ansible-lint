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
from pathlib import Path

import pytest

from ansiblelint import cli, constants, utils
from ansiblelint.__main__ import initialize_logger
from ansiblelint.file_utils import normpath


@pytest.mark.parametrize(('string', 'expected_cmd', 'expected_args', 'expected_kwargs'), (
    pytest.param('', '', [], {}, id='blank'),
    pytest.param('vars:', 'vars', [], {}, id='single_word'),
    pytest.param('hello: a=1', 'hello', [], {'a': '1'}, id='string_module_and_arg'),
    pytest.param('action: hello a=1', 'hello', [], {'a': '1'}, id='strips_action'),
    pytest.param('action: whatever bobbins x=y z=x c=3',
                 'whatever',
                 ['bobbins', 'x=y', 'z=x', 'c=3'],
                 {},
                 id='more_than_one_arg'),
    pytest.param('action: command chdir=wxy creates=zyx tar xzf zyx.tgz',
                 'command',
                 ['tar', 'xzf', 'zyx.tgz'],
                 {'chdir': 'wxy', 'creates': 'zyx'},
                 id='command_with_args'),
))
def test_tokenize(string, expected_cmd, expected_args, expected_kwargs):
    """Test that tokenize works for different input types."""
    (cmd, args, kwargs) = utils.tokenize(string)
    assert cmd == expected_cmd
    assert args == expected_args
    assert kwargs == expected_kwargs


@pytest.mark.parametrize(('reference_form', 'alternate_forms'), (
    pytest.param(dict(name='hello', action='command chdir=abc echo hello world'),
                 (dict(name="hello", command="chdir=abc echo hello world"), ),
                 id='simple_command'),
    pytest.param({'git': {'version': 'abc'}, 'args': {'repo': 'blah', 'dest': 'xyz'}},
                 ({'git': {'version': 'abc', 'repo': 'blah', 'dest': 'xyz'}},
                  {"git": 'version=abc repo=blah dest=xyz'},
                  {"git": None, "args": {'repo': 'blah', 'dest': 'xyz', 'version': 'abc'}},
                  ),
                 id='args')
))
def test_normalize(reference_form, alternate_forms):
    """Test that tasks specified differently are normalized same way."""
    normal_form = utils.normalize_task(reference_form, 'tasks.yml')

    for form in alternate_forms:
        assert normal_form == utils.normalize_task(form, 'tasks.yml')


def test_normalize_complex_command():
    """Test that tasks specified differently are normalized same way."""
    task1 = dict(name="hello", action={'module': 'pip',
                                       'name': 'df',
                                       'editable': 'false'})
    task2 = dict(name="hello", pip={'name': 'df',
                                    'editable': 'false'})
    task3 = dict(name="hello", pip="name=df editable=false")
    task4 = dict(name="hello", action="pip name=df editable=false")
    assert utils.normalize_task(task1, 'tasks.yml') == utils.normalize_task(task2, 'tasks.yml')
    assert utils.normalize_task(task2, 'tasks.yml') == utils.normalize_task(task3, 'tasks.yml')
    assert utils.normalize_task(task3, 'tasks.yml') == utils.normalize_task(task4, 'tasks.yml')


def test_extract_from_list():
    """Check that tasks get extracted from blocks if present."""
    block = {
        'block': [{'tasks': {'name': 'hello', 'command': 'whoami'}}],
        'test_none': None,
        'test_string': 'foo',
    }
    blocks = [block]

    test_list = utils.extract_from_list(blocks, ['block'])
    test_none = utils.extract_from_list(blocks, ['test_none'])

    assert list(block['block']) == test_list
    assert list() == test_none
    with pytest.raises(RuntimeError):
        utils.extract_from_list(blocks, ['test_string'])


@pytest.mark.parametrize(('template', 'output'), (
    pytest.param('{{ playbook_dir }}', '/a/b/c', id='simple'),
    pytest.param("{{ 'hello' | doesnotexist }}",
                 "{{ 'hello' | doesnotexist }}",
                 id='unknown_filter'),
    pytest.param('{{ hello | to_json }}',
                 '{{ hello | to_json }}',
                 id='to_json_filter_on_undefined_variable'),
    pytest.param('{{ hello | to_nice_yaml }}',
                 '{{ hello | to_nice_yaml }}',
                 id='to_nice_yaml_filter_on_undefined_variable'),
))
def test_template(template, output):
    """Verify that resolvable template vars and filters get rendered."""
    result = utils.template('/base/dir', template, dict(playbook_dir='/a/b/c'))
    assert result == output


def test_task_to_str_unicode():
    """Ensure that extracting messages from tasks preserves Unicode."""
    task = dict(fail=dict(msg=u"unicode é ô à"))
    result = utils.task_to_str(utils.normalize_task(task, 'filename.yml'))
    assert result == u"fail msg=unicode é ô à"


@pytest.mark.parametrize('path', (
    pytest.param(Path('a/b/../'), id='pathlib.Path'),
    pytest.param('a/b/../', id='str'),
))
def test_normpath_with_path_object(path):
    """Ensure that relative parent dirs are normalized in paths."""
    assert normpath(path) == "a"


def test_expand_path_vars(monkeypatch):
    """Ensure that tilde and env vars are expanded in paths."""
    test_path = '/test/path'
    monkeypatch.setenv('TEST_PATH', test_path)
    assert utils.expand_path_vars('~') == os.path.expanduser('~')
    assert utils.expand_path_vars('$TEST_PATH') == test_path


@pytest.mark.parametrize(('test_path', 'expected'), (
    pytest.param(Path('$TEST_PATH'), "/test/path", id='pathlib.Path'),
    pytest.param('$TEST_PATH', "/test/path", id='str'),
    pytest.param('  $TEST_PATH  ', "/test/path", id='stripped-str'),
    pytest.param('~', os.path.expanduser('~'), id='home'),
))
def test_expand_paths_vars(test_path, expected, monkeypatch):
    """Ensure that tilde and env vars are expanded in paths lists."""
    monkeypatch.setenv('TEST_PATH', '/test/path')
    assert utils.expand_paths_vars([test_path]) == [expected]


@pytest.mark.parametrize(
    ('reset_env_var', 'message_prefix'),
    (
        ('PATH',
            "Failed to locate command: "),
        ('GIT_DIR',
            "Failed to discover yaml files to lint using git: ")
    ),
    ids=('no Git installed', 'outside Git repository'),
)
def test_get_yaml_files_git_verbose(
    reset_env_var,
    message_prefix,
    monkeypatch,
    caplog
):
    """Ensure that autodiscovery lookup failures are logged."""
    options = cli.get_config(['-v'])
    initialize_logger(options.verbosity)
    monkeypatch.setenv(reset_env_var, '')
    utils.get_yaml_files(options)

    expected_info = (
        "ansiblelint.utils",
        logging.INFO,
        'Discovering files to lint: git ls-files *.yaml *.yml')

    assert expected_info in caplog.record_tuples
    assert any(m.startswith(message_prefix) for m in caplog.messages)


@pytest.mark.parametrize(
    'is_in_git',
    (True, False),
    ids=('in Git', 'outside Git'),
)
def test_get_yaml_files_silent(is_in_git, monkeypatch, capsys):
    """Verify that no stderr output is displayed while discovering yaml files.

    (when the verbosity is off, regardless of the Git or Git-repo presence)

    Also checks expected number of files are detected.
    """
    options = cli.get_config([])
    test_dir = Path(__file__).resolve().parent
    lint_path = test_dir / 'roles' / 'test-role'
    if not is_in_git:
        monkeypatch.setenv('GIT_DIR', '')

    yaml_count = (
        len(list(lint_path.glob('**/*.yml'))) + len(list(lint_path.glob('**/*.yaml')))
    )

    monkeypatch.chdir(str(lint_path))
    files = utils.get_yaml_files(options)
    stderr = capsys.readouterr().err
    assert not stderr, 'No stderr output is expected when the verbosity is off'
    assert len(files) == yaml_count, (
        "Expected to find {yaml_count} yaml files in {lint_path}".format_map(
            locals(),
        )
    )


def test_logger_debug(caplog):
    """Test that the double verbosity arg causes logger to be DEBUG."""
    options = cli.get_config(['-vv'])
    initialize_logger(options.verbosity)

    expected_info = (
        "ansiblelint.__main__",
        logging.DEBUG,
        'Logging initialized to level 10',
    )

    assert expected_info in caplog.record_tuples


def test_cli_auto_detect(capfd):
    """Test that run without arguments it will detect and lint the entire repository."""
    cmd = sys.executable, "-m", "ansiblelint", "-v", "-p", "--nocolor"
    result = subprocess.run(cmd, check=False).returncode

    # We de expect to fail on our own repo due to test examples we have
    # TODO(ssbarnea) replace it with exact return code once we document them
    assert result != 0

    out, err = capfd.readouterr()

    # Confirmation that it runs in auto-detect mode
    assert "Discovering files to lint: git ls-files *.yaml *.yml" in err
    # Expected failure to detect file type"
    assert "Unknown file type: test/fixtures/unknown-type.yml" in err
    # An expected rule match from our examples
    assert "examples/roles/bobbins/tasks/main.yml:2: " \
        "[E401] Git checkouts must contain explicit version" in out
    # assures that our .ansible-lint exclude was effective in excluding github files
    assert "Unknown file type: .github/" not in out


def test_auto_detect_exclude(monkeypatch):
    """Verify that exclude option can be used to narrow down detection."""
    options = cli.get_config(['--exclude', 'foo'])

    def mockreturn(options):
        return ['foo/playbook.yml', 'bar/playbook.yml']

    monkeypatch.setattr(utils, 'get_yaml_files', mockreturn)
    result = utils.get_playbooks_and_roles(options)
    assert result == ['bar/playbook.yml']


_DEFAULT_RULEDIRS = [constants.DEFAULT_RULESDIR]
_CUSTOM_RULESDIR = Path(__file__).parent / "custom_rules"
_CUSTOM_RULEDIRS = [
    str(_CUSTOM_RULESDIR / "example_inc"),
    str(_CUSTOM_RULESDIR / "example_com")
]


@pytest.mark.parametrize(("user_ruledirs", "use_default", "expected"), (
    ([], True, _DEFAULT_RULEDIRS),
    ([], False, _DEFAULT_RULEDIRS),
    (_CUSTOM_RULEDIRS, True, _CUSTOM_RULEDIRS + _DEFAULT_RULEDIRS),
    (_CUSTOM_RULEDIRS, False, _CUSTOM_RULEDIRS)
))
def test_get_rules_dirs(user_ruledirs, use_default, expected):
    """Test it returns expected dir lists."""
    assert utils.get_rules_dirs(user_ruledirs, use_default) == expected


@pytest.mark.parametrize(("user_ruledirs", "use_default", "expected"), (
    ([], True, sorted(_CUSTOM_RULEDIRS) + _DEFAULT_RULEDIRS),
    ([], False, sorted(_CUSTOM_RULEDIRS) + _DEFAULT_RULEDIRS),
    (_CUSTOM_RULEDIRS, True,
     _CUSTOM_RULEDIRS + sorted(_CUSTOM_RULEDIRS) + _DEFAULT_RULEDIRS),
    (_CUSTOM_RULEDIRS, False, _CUSTOM_RULEDIRS)
))
def test_get_rules_dirs_with_custom_rules(user_ruledirs, use_default, expected, monkeypatch):
    """Test it returns expected dir lists when custom rules exist."""
    monkeypatch.setenv(constants.CUSTOM_RULESDIR_ENVVAR, str(_CUSTOM_RULESDIR))
    assert utils.get_rules_dirs(user_ruledirs, use_default) == expected
