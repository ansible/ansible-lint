import pytest

from ansiblelint.testing import RunFromText

PLAYBOOK_PRE_TASKS = '''\
- hosts: all
  tasks:
    - name: bad git 1  # noqa git-latest
      action: git a=b c=d
    - name: bad git 2
      action: git a=b c=d
  pre_tasks:
    - name: bad git 3  # noqa git-latest
      action: git a=b c=d
    - name: bad git 4
      action: git a=b c=d
'''

PLAYBOOK_POST_TASKS = '''\
- hosts: all
  tasks:
    - name: bad git 1  # noqa git-latest
      action: git a=b c=d
    - name: bad git 2
      action: git a=b c=d
  post_tasks:
    - name: bad git 3  # noqa git-latest
      action: git a=b c=d
    - name: bad git 4
      action: git a=b c=d
'''

PLAYBOOK_HANDLERS = '''\
- hosts: all
  tasks:
    - name: bad git 1  # noqa git-latest
      action: git a=b c=d
    - name: bad git 2
      action: git a=b c=d
  handlers:
    - name: bad git 3  # noqa git-latest
      action: git a=b c=d
    - name: bad git 4
      action: git a=b c=d
'''

PLAYBOOK_TWO_PLAYS = '''\
- hosts: all
  tasks:
    - name: bad git 1  # noqa git-latest
      action: git a=b c=d
    - name: bad git 2
      action: git a=b c=d

- hosts: all
  tasks:
    - name: bad git 3  # noqa git-latest
      action: git a=b c=d
    - name: bad git 4
      action: git a=b c=d
'''

PLAYBOOK_WITH_BLOCK = '''\
- hosts: all
  tasks:
    - name: bad git 1  # noqa git-latest
      action: git a=b c=d
    - name: bad git 2
      action: git a=b c=d
    - name: Block with rescue and always section
      block:
        - name: bad git 3  # noqa git-latest
          action: git a=b c=d
        - name: bad git 4
          action: git a=b c=d
      rescue:
        - name: bad git 5  # noqa git-latest
          action: git a=b c=d
        - name: bad git 6
          action: git a=b c=d
      always:
        - name: bad git 7  # noqa git-latest
          action: git a=b c=d
        - name: bad git 8
          action: git a=b c=d
'''


@pytest.mark.parametrize(
    ('playbook', 'length'),
    (
        pytest.param(PLAYBOOK_PRE_TASKS, 2, id='PRE_TASKS'),
        pytest.param(PLAYBOOK_POST_TASKS, 2, id='POST_TASKS'),
        pytest.param(PLAYBOOK_HANDLERS, 2, id='HANDLERS'),
        pytest.param(PLAYBOOK_TWO_PLAYS, 2, id='TWO_PLAYS'),
        pytest.param(PLAYBOOK_WITH_BLOCK, 4, id='WITH_BLOCK'),
    ),
)
def test_pre_tasks(
    default_text_runner: RunFromText, playbook: str, length: int
) -> None:
    """Check that skipping is possible in different playbook parts."""
    # When
    results = default_text_runner.run_playbook(playbook)

    # Then
    assert len(results) == length
