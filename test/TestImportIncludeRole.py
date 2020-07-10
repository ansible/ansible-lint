import pytest

from ansiblelint.runner import Runner

ROLE_TASKS_MAIN = '''
- name: shell instead of command
  shell: echo hello world
'''

ROLE_TASKS_WORLD = '''
- command: echo this is a task without a name
'''

PLAY_IMPORT_ROLE = '''
- hosts: all

  tasks:
    - import_role:
        name: test-role
'''

PLAY_IMPORT_ROLE_INCOMPLETE = '''
- hosts: all

  tasks:
    - import_role:
        foo: bar
'''

PLAY_IMPORT_ROLE_INLINE = '''
- hosts: all

  tasks:
    - import_role: name=test-role
'''

PLAY_INCLUDE_ROLE = '''
- hosts: all

  tasks:
    - include_role:
        name: test-role
        tasks_from: world
'''

PLAY_INCLUDE_ROLE_INLINE = '''
- hosts: all

  tasks:
    - include_role: name=test-role tasks_from=world
'''


@pytest.fixture
def playbook_path(request, tmp_path):
    playbook_text = request.param
    role_tasks_dir = tmp_path / 'test-role' / 'tasks'
    role_tasks_dir.mkdir(parents=True)
    (role_tasks_dir / 'main.yml').write_text(ROLE_TASKS_MAIN)
    (role_tasks_dir / 'world.yml').write_text(ROLE_TASKS_WORLD)
    play_path = tmp_path / 'playbook.yml'
    play_path.write_text(playbook_text)
    return str(play_path)


@pytest.mark.parametrize(('playbook_path', 'messages'), (
    pytest.param(PLAY_IMPORT_ROLE,
                 ['only when shell functionality is required'],
                 id='IMPORT_ROLE',
                 ),
    pytest.param(PLAY_IMPORT_ROLE_INLINE,
                 ['only when shell functionality is require'],
                 id='IMPORT_ROLE_INLINE',
                 ),
    pytest.param(PLAY_INCLUDE_ROLE,
                 ['only when shell functionality is require',
                  'All tasks should be named'],
                 id='INCLUDE_ROLE',
                 ),
    pytest.param(PLAY_INCLUDE_ROLE_INLINE,
                 ['only when shell functionality is require',
                  'All tasks should be named'],
                 id='INCLUDE_ROLE_INLINE',
                 ),
), indirect=('playbook_path', ))
def test_import_role2(default_rules_collection, playbook_path, messages):
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    results = runner.run()
    for message in messages:
        assert message in str(results)


@pytest.mark.parametrize(('playbook_path', 'messages'), (
    pytest.param(PLAY_IMPORT_ROLE_INCOMPLETE,
                 ["Failed to find required 'name' key in import_role"],
                 id='IMPORT_ROLE_INCOMPLETE',
                 ),
), indirect=('playbook_path', ))
def test_invalid_import_role(default_rules_collection, playbook_path, messages):
    runner = Runner(default_rules_collection, playbook_path, [], [], [])
    results = runner.run()
    for message in messages:
        assert message in str(results)
