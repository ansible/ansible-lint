"""Tests for nested-jinja rule."""
# Author: Adrián Tóth <adtoth@redhat.com>
#
# Copyright (c) 2020, Red Hat, Inc.
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
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from ansiblelint.file_utils import Lintable
from ansiblelint.runner import Runner

FAIL_TASK_1LN = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: One-level nesting
      ansible.builtin.set_fact:
        var_one: "2*(1+2) is {{ 2 * {{ 1 + 2 }} }}"
""",
)

FAIL_TASK_1LN_M = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: One-level multiline nesting
      ansible.builtin.set_fact:
        var_one_ml: >
          2*(1+2) is {{ 2 *
          {{ 1 + 2 }}
          }}
""",
)

FAIL_TASK_2LN = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Two-level nesting
      ansible.builtin.set_fact:
        var_two: "2*(1+(3-1)) is {{ 2 * {{ 1 + {{ 3 - 1 }}}} }}"
""",
)

FAIL_TASK_2LN_M = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Two-level multiline nesting
      ansible.builtin.set_fact:
        var_two_ml: >
          2*(1+(3-1)) is {{ 2 *
          {{ 1 +
          {{ 3 - 1 }}
          }} }}
""",
)

FAIL_TASK_W_5LN = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Five-level wild nesting
      ansible.builtin.set_fact:
        var_three_wld: "{{ {{ {{ {{ {{ 234 }} }} }} }} }}"
""",
)

FAIL_TASK_W_5LN_M = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Five-level wild multiline nesting
      ansible.builtin.set_fact:
        var_three_wld_ml: >
          {{
          {{
          {{
          {{
          {{ 234 }}
          }}
          }}
          }}
          }}
""",
)

SUCCESS_TASK_P = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Non-nested example
      ansible.builtin.set_fact:
        var_one: "number for 'one' is {{ 2 * 1 }}"
""",
)

SUCCESS_TASK_P_M = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Multiline non-nested example
      ansible.builtin.set_fact:
        var_one_ml: >
          number for 'one' is {{
          2 * 1 }}
""",
)

SUCCESS_TASK_2P = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Nesting far from each other
      ansible.builtin.set_fact:
        var_two: "number for 'two' is {{ 2 * 1 }} and number for 'three' is {{ 4 - 1 }}"
""",
)

SUCCESS_TASK_2P_M = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Multiline nesting far from each other
      ansible.builtin.set_fact:
        var_two_ml: >
          number for 'two' is {{ 2 * 1
          }} and number for 'three' is {{
          4 - 1 }}
""",
)

SUCCESS_TASK_C_2P = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Nesting close to each other
      ansible.builtin.set_fact:
        var_three: "number for 'ten' is {{ 2 - 1 }}{{ 3 - 3 }}"
""",
)

SUCCESS_TASK_C_2P_M = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Multiline nesting close to each other
      ansible.builtin.set_fact:
        var_three_ml: >
          number for 'ten' is {{
          2 - 1
          }}{{ 3 - 3 }}
""",
)

SUCCESS_TASK_PRINT = Lintable(
    "playbook.yml",
    """\
---
- name: Fixture
  hosts: all
  tasks:
    - name: Print curly braces
      ansible.builtin.debug:
        msg: docker image inspect my_image --format='{{ '{{' }}.Size{{ '}}' }}'
""",
)


@pytest.fixture
def _playbook_file(tmp_path: Path, request: SubRequest) -> None:
    if request.param is None:
        return
    for play_file in request.param:
        path = tmp_path / play_file.name
        path.write_text(play_file.content)


@pytest.mark.parametrize(
    "_playbook_file",
    (
        pytest.param([FAIL_TASK_1LN], id="one-level nesting"),
        pytest.param([FAIL_TASK_1LN_M], id="one-level multiline nesting"),
        pytest.param([FAIL_TASK_2LN], id="two-level nesting"),
        pytest.param([FAIL_TASK_2LN_M], id="two-level multiline nesting"),
        pytest.param([FAIL_TASK_W_5LN], id="five-level wild nesting"),
        pytest.param([FAIL_TASK_W_5LN_M], id="five-level wild multiline nesting"),
    ),
    indirect=["_playbook_file"],
)
@pytest.mark.usefixtures("_playbook_file")
def test_including_wrong_nested_jinja(runner: Runner) -> None:
    """Check that broken Jinja nesting produces a violation."""
    found = False
    for match in runner.run():
        if match.rule.id == "no-jinja-nesting":
            found = True
            break
    assert found, "Failed to spot no-jinja-nesting in test results."


@pytest.mark.parametrize(
    "_playbook_file",
    (
        pytest.param(
            # file includes non-nested example
            [SUCCESS_TASK_P],
            id="1",
        ),
        pytest.param(
            # file includes multiline non-nested example
            [SUCCESS_TASK_P_M],
            id="2",
        ),
        pytest.param(
            # file includes nesting far from each other
            [SUCCESS_TASK_2P],
            id="3",
        ),
        pytest.param(
            # file includes multiline nesting far from each other
            [SUCCESS_TASK_2P_M],
            id="4",
        ),
        pytest.param(
            # file includes nesting close to each other
            [SUCCESS_TASK_C_2P],
            id="5",
        ),
        pytest.param(
            # file includes multiline nesting close to each other
            [SUCCESS_TASK_C_2P_M],
            id="6",
        ),
        pytest.param(
            # file includes print curly braces
            [SUCCESS_TASK_PRINT],
            id="7",
        ),
    ),
    indirect=["_playbook_file"],
)
@pytest.mark.usefixtures("_playbook_file")
def test_including_proper_nested_jinja(runner: Runner) -> None:
    """Check that properly balanced Jinja nesting doesn't fail."""
    rule_violations = runner.run()
    assert not rule_violations
