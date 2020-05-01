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

import logging
from pathlib import Path

from importlib_metadata import version as get_dist_version
from packaging.version import Version
import pytest

import ansiblelint.utils as utils
from ansiblelint import cli


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
    normal_form = utils.normalize_task(reference_form, 'tasks.yml')

    for form in alternate_forms:
        assert normal_form == utils.normalize_task(form, 'tasks.yml')


@pytest.mark.xfail(
    Version(get_dist_version('ansible')) >= Version('2.10.dev0') and
    Version(get_dist_version('ansible-base')) >= Version('2.10.dev0'),
    reason='Post-split Ansible Core Engine does not have '
    'the module used in the test playbook.'
    ' Ref: https://github.com/ansible/ansible-lint/issues/703.'
    ' Ref: https://github.com/ansible/ansible/pull/68598.',
    raises=SystemExit,
    strict=True,
)
def test_normalize_complex_command():
    task1 = dict(name="hello", action={'module': 'ec2',
                                       'region': 'us-east1',
                                       'etc': 'whatever'})
    task2 = dict(name="hello", ec2={'region': 'us-east1',
                                    'etc': 'whatever'})
    task3 = dict(name="hello", ec2="region=us-east1 etc=whatever")
    task4 = dict(name="hello", action="ec2 region=us-east1 etc=whatever")
    assert utils.normalize_task(task1, 'tasks.yml') == utils.normalize_task(task2, 'tasks.yml')
    assert utils.normalize_task(task2, 'tasks.yml') == utils.normalize_task(task3, 'tasks.yml')
    assert utils.normalize_task(task3, 'tasks.yml') == utils.normalize_task(task4, 'tasks.yml')


def test_extract_from_list():
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
    result = utils.template('/base/dir', template, dict(playbook_dir='/a/b/c'))
    assert result == output


def test_task_to_str_unicode():
    task = dict(fail=dict(msg=u"unicode é ô à"))
    result = utils.task_to_str(utils.normalize_task(task, 'filename.yml'))
    assert result == u"fail msg=unicode é ô à"


@pytest.mark.parametrize('path', (
    pytest.param(Path('a/b/../'), id='pathlib.Path'),
    pytest.param('a/b/../', id='str'),
))
def test_normpath_with_path_object(path):
    assert utils.normpath(path) == "a"


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
    options = cli.get_config(['-v'])
    utils.initialize_logger(options.verbosity)
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
