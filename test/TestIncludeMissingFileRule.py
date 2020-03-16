from __future__ import print_function

import os
import pytest

from ansiblelint import Runner, RulesCollection

PLAY_INCLUDING = '''
- hosts: all
  tasks:
    - include: some_file.yml
'''

PLAY_INCLUDING_JINJA2 = '''
- hosts: all
  tasks:
    - include: "{{ some_path }}/some_file.yml"
'''

PLAY_INCLUDING_NOQA = '''
- hosts: all
  tasks:
    - include: some_file.yml # noqa 505
'''

PLAY_INCLUDED = '''
- debug:
    msg: 'was found & included'
'''


@pytest.fixture
def linter_rules(scope="module"):
    rules_directory = os.path.join('lib', 'ansiblelint', 'rules')
    rules = RulesCollection([rules_directory])
    return rules


@pytest.fixture
def including_playbook(tmp_path):
    print('including_playbook', type(tmp_path))

    with open(os.path.join(tmp_path, 'playbook.yml'), 'w') as f_play:
        f_play.write(PLAY_INCLUDING)
    yield f_play
    print('-------------------tear down including_playbook')


@pytest.fixture
def including_playbook_noqa(tmp_path):
    print('including_playbook', tmp_path)
    with open(os.path.join(tmp_path, 'playbook.yml'), 'w') as f_play:
        f_play.write(PLAY_INCLUDING_NOQA)
    yield f_play
    print('-------------------tear down including_playbook_noqa')


@pytest.fixture
def including_playbook_jinja2(tmp_path):
    print('including_playbook', tmp_path)
    with open(os.path.join(tmp_path, 'playbook.yml'), 'w') as f_play:
        f_play.write(PLAY_INCLUDING_JINJA2)
    yield f_play
    print('-------------------tear down including_playbook_jinja')


@pytest.fixture
def included_playbook(tmp_path):
    print('included_playbook', tmp_path)
    with open(os.path.join(tmp_path, 'some_file.yml'), 'w') as f_play:
        f_play.write(PLAY_INCLUDED)
    yield f_play
    print('-------------------tear down included_playbook')


def test_include_missing_file(linter_rules, including_playbook):
    runner = Runner(linter_rules, including_playbook.name, [], [], [])
    results = runner.run()
    assert 'referenced missing file in' in str(results)
    assert 'playbook.yml:2' in str(results)
    assert 'some_file.yml' in str(results)


def test_include_found_file(linter_rules, including_playbook, included_playbook):
    runner = Runner(linter_rules, including_playbook.name, [], [], [])
    results = runner.run()
    assert 'referenced missing file in' not in str(results)


def test_include_noqa_working(linter_rules, including_playbook_noqa):
    runner = Runner(linter_rules, including_playbook_noqa.name, [], [], [])
    results = runner.run()
    assert 'referenced missing file in' not in str(results)


def test_include_omit_templated_references(linter_rules, including_playbook_jinja2):
    runner = Runner(linter_rules, including_playbook_jinja2.name, [], [], [])
    results = runner.run()
    assert 'referenced missing file in' not in str(results)
