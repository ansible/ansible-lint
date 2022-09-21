"""Validate ansiblelint.skip_utils."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from ansiblelint.constants import SKIPPED_RULES_KEY
from ansiblelint.file_utils import Lintable
from ansiblelint.skip_utils import (
    append_skipped_rules,
    get_rule_skips_from_line,
    is_nested_task,
)
from ansiblelint.testing import RunFromText

if TYPE_CHECKING:
    from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject

PLAYBOOK_WITH_NOQA = """\
---
- name: Fixture
  hosts: all
  vars:
    SOME_VAR_NOQA: "Foo"  # noqa var-naming
    SOME_VAR: "Bar"
  tasks:
    - name: "Set the SOME_OTHER_VAR"
      ansible.builtin.set_fact:
        SOME_OTHER_VAR_NOQA: "Baz"  # noqa var-naming
        SOME_OTHER_VAR: "Bat"
"""


@pytest.mark.parametrize(
    ("line", "expected"),
    (
        ("foo # noqa: bar", "bar"),
        ("foo # noqa bar", "bar"),
    ),
)
def test_get_rule_skips_from_line(line: str, expected: str) -> None:
    """Validate get_rule_skips_from_line."""
    v = get_rule_skips_from_line(line)
    assert v == [expected]


def test_playbook_noqa(default_text_runner: RunFromText) -> None:
    """Check that noqa is properly taken into account on vars and tasks."""
    results = default_text_runner.run_playbook(PLAYBOOK_WITH_NOQA)
    # Should raise error at "SOME_VAR".
    assert len(results) == 1


@pytest.mark.parametrize(
    ("lintable", "yaml", "expected_form"),
    (
        pytest.param(
            Lintable("examples/playbooks/noqa.yml", kind="playbook"),
            [
                {
                    "hosts": "localhost",
                    "tasks": [
                        {
                            "name": "This would typically fire latest[git] and partial-become",
                            "become_user": "alice",
                            "git": "src=/path/to/git/repo dest=checkout",
                            "__line__": 4,
                            "__file__": Path("examples/playbooks/noqa.yml"),
                        }
                    ],
                    "__line__": 2,
                    "__file__": Path("examples/playbooks/noqa.yml"),
                }
            ],
            [
                {
                    "hosts": "localhost",
                    "tasks": [
                        {
                            "name": "This would typically fire latest[git] and partial-become",
                            "become_user": "alice",
                            "git": "src=/path/to/git/repo dest=checkout",
                            "__line__": 4,
                            "__file__": Path("examples/playbooks/noqa.yml"),
                            SKIPPED_RULES_KEY: ["latest[git]", "partial-become"],
                        }
                    ],
                    "__line__": 2,
                    "__file__": Path("examples/playbooks/noqa.yml"),
                }
            ],
        ),
        pytest.param(
            Lintable("examples/playbooks/noqa-nested.yml", kind="playbook"),
            [
                {
                    "hosts": "localhost",
                    "tasks": [
                        {
                            "name": "Example of multi-level block",
                            "block": [
                                {
                                    "name": "2nd level",
                                    "block": [
                                        {
                                            "ansible.builtin.debug": {
                                                "msg": "Test unnamed task in block",
                                                "__line__": 9,
                                                "__file__": Path(
                                                    "examples/playbooks/noqa-nested.yml"
                                                ),
                                            },
                                            "__line__": 8,
                                            "__file__": Path(
                                                "examples/playbooks/noqa-nested.yml"
                                            ),
                                        }
                                    ],
                                    "__line__": 6,
                                    "__file__": Path(
                                        "examples/playbooks/noqa-nested.yml"
                                    ),
                                }
                            ],
                            "__line__": 4,
                            "__file__": Path("examples/playbooks/noqa-nested.yml"),
                        }
                    ],
                    "__line__": 2,
                    "__file__": Path("examples/playbooks/noqa-nested.yml"),
                }
            ],
            [
                {
                    "hosts": "localhost",
                    "tasks": [
                        {
                            "name": "Example of multi-level block",
                            "block": [
                                {
                                    "name": "2nd level",
                                    "block": [
                                        {
                                            "ansible.builtin.debug": {
                                                "msg": "Test unnamed task in block",
                                                "__line__": 9,
                                                "__file__": Path(
                                                    "examples/playbooks/noqa-nested.yml"
                                                ),
                                            },
                                            "__line__": 8,
                                            "__file__": Path(
                                                "examples/playbooks/noqa-nested.yml"
                                            ),
                                            SKIPPED_RULES_KEY: ["name[missing]"],
                                        }
                                    ],
                                    "__line__": 6,
                                    "__file__": Path(
                                        "examples/playbooks/noqa-nested.yml"
                                    ),
                                    SKIPPED_RULES_KEY: ["name[missing]"],
                                }
                            ],
                            "__line__": 4,
                            "__file__": Path("examples/playbooks/noqa-nested.yml"),
                            SKIPPED_RULES_KEY: ["name[missing]"],
                        }
                    ],
                    "__line__": 2,
                    "__file__": Path("examples/playbooks/noqa-nested.yml"),
                }
            ],
        ),
    ),
)
def test_append_skipped_rules(
    lintable: Lintable,
    yaml: AnsibleBaseYAMLObject,
    expected_form: AnsibleBaseYAMLObject,
) -> None:
    """Check that it appends skipped_rules properly."""
    assert append_skipped_rules(yaml, lintable) == expected_form


@pytest.mark.parametrize(
    ("task", "expected"),
    (
        pytest.param(
            dict(
                name="ensure apache is at the latest version",
                yum={"name": "httpd", "state": "latest"},
            ),
            False,
        ),
        pytest.param(
            dict(
                name="Attempt and graceful roll back",
                block=[
                    {"name": "Force a failure", "ansible.builtin.command": "/bin/false"}
                ],
                rescue=[
                    {
                        "name": "Force a failure in middle of recovery!",
                        "ansible.builtin.command": "/bin/false",
                    }
                ],
                always=[
                    {
                        "name": "Always do this",
                        "ansible.builtin.debug": {"msg": "This always executes"},
                    }
                ],
            ),
            True,
        ),
    ),
)
def test_is_nested_task(task: dict[str, Any], expected: bool) -> None:
    """Test is_nested_task() returns expected bool."""
    assert is_nested_task(task) == expected
