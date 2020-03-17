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


@pytest.fixture(scope='module')
def linter_rules():
    rules_directory = os.path.join('lib', 'ansiblelint', 'rules')
    rules = RulesCollection([rules_directory])
    return rules


@pytest.fixture
def including_playbook(tmp_path):
    with open(os.path.join(str(tmp_path), 'playbook.yml'), 'w') as f_play:
        f_play.write(PLAY_INCLUDING)
    return f_play


@pytest.fixture
def including_playbook_noqa(tmp_path):
    with open(os.path.join(str(tmp_path), 'playbook.yml'), 'w') as f_play:
        f_play.write(PLAY_INCLUDING_NOQA)
    return f_play


@pytest.fixture
def including_playbook_jinja2(tmp_path):
    with open(os.path.join(str(tmp_path), 'playbook.yml'), 'w') as f_play:
        f_play.write(PLAY_INCLUDING_JINJA2)
    return f_play


@pytest.fixture
def included_playbook(tmp_path):
    with open(os.path.join(str(tmp_path), 'some_file.yml'), 'w') as f_play:
        f_play.write(PLAY_INCLUDED)
    return f_play


def test_include_missing_file(linter_rules, including_playbook):
    runner = Runner(linter_rules, including_playbook.name, [], [], [])
    results = str(runner.run())
    assert 'referenced missing file in' in results
    assert 'playbook.yml:2' in results
    assert 'some_file.yml' in results


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
