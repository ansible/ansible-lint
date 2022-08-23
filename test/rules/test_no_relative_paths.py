"""Tests for no-relative-paths rule."""
from ansiblelint.rules import RulesCollection
from ansiblelint.rules.no_relative_paths import RoleRelativePath
from ansiblelint.testing import RunFromText

FAIL_TASKS = """
- name: Template example
  template:
    src: ../templates/foo.j2
    dest: /etc/file.conf
- name: Copy example
  copy:
    src: ../files/foo.conf
    dest: /etc/foo.conf
# Removed from test suite as module is no longer part of core
# - name: Some win_template example
#   win_template:
#     src: ../win_templates/file.conf.j2
#     dest: file.conf
# - name: Some win_copy example
#   win_copy:
#     src: ../files/foo.conf
#     dest: renamed-foo.conf
"""

SUCCESS_TASKS = """
- name: Content example with no src
  copy:
    content: '# This file was moved to /etc/other.conf'
    dest: /etc/mine.conf
# - name: Content example with no src
#   win_copy:
#     content: '# This file was moved to /etc/other.conf'
#     dest: /etc/mine.conf
"""


def test_no_relative_paths_fail() -> None:
    """Negative test for no-relative-paths."""
    collection = RulesCollection()
    collection.register(RoleRelativePath())
    runner = RunFromText(collection)
    results = runner.run_role_tasks_main(FAIL_TASKS)
    assert len(results) == 2


def test_no_relative_paths_success() -> None:
    """Positive test for no-relative-paths."""
    collection = RulesCollection()
    collection.register(RoleRelativePath())
    runner = RunFromText(collection)
    results = runner.run_role_tasks_main(SUCCESS_TASKS)
    assert len(results) == 0
