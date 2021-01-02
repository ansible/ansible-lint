import pytest

from ansiblelint.file_utils import Lintable

PLAY_INCLUDING_PLAIN = Lintable('playbook.yml', u'''\
- hosts: all
  tasks:
    - include: some_file.yml
''')

PLAY_INCLUDING_JINJA2 = Lintable('playbook.yml', u'''\
- hosts: all
  tasks:
    - include: "{{ some_path }}/some_file.yml"
''')

PLAY_INCLUDING_NOQA = Lintable('playbook.yml', u'''\
- hosts: all
  tasks:
    - include: some_file.yml # noqa 505
''')

PLAY_INCLUDED = Lintable('some_file.yml', u'''\
- debug:
    msg: 'was found & included'
''')

PLAY_HAVING_TASK = Lintable('playbook.yml', u'''\
- name: Play
  hosts: all
  pre_tasks:
  tasks:
    - name: Ping
      ping:
''')


@pytest.mark.parametrize(
    '_play_files', (pytest.param([PLAY_INCLUDING_PLAIN], id='referenced file missing'), ),
    indirect=['_play_files']
)
@pytest.mark.usefixtures('_play_files')
def test_include_file_missing(runner):
    results = str(runner.run())
    assert 'referenced files must exist' in results
    assert 'playbook.yml' in results
    assert 'some_file.yml' in results


@pytest.mark.parametrize(
    '_play_files',
    (
        # pytest.param([PLAY_INCLUDING_PLAIN, PLAY_INCLUDED], id='File Exists'),
        pytest.param([PLAY_INCLUDING_JINJA2], id='JINJA2 in reference'),
        pytest.param([PLAY_INCLUDING_NOQA], id='NOQA was used'),
        pytest.param([PLAY_HAVING_TASK], id='Having a task')
    ),
    indirect=['_play_files']
)
@pytest.mark.usefixtures('_play_files')
def test_cases_that_do_not_report(runner):
    results = str(runner.run())
    assert 'referenced missing file in' not in results
