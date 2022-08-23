"""Tests for literal-compare rule."""
import pytest

from ansiblelint.rules import RulesCollection
from ansiblelint.rules.literal_compare import ComparisonToLiteralBoolRule
from ansiblelint.testing import RunFromText

PASS_WHEN = """
- name: Example task
  debug:
    msg: test
  when: my_var

- name: Another example task
  debug:
    msg: test
  when:
    - 1 + 1 == 2
    - true
"""

PASS_WHEN_NOT_FALSE = """
- name: Example task
  debug:
    msg: test
  when: not my_var
"""

PASS_WHEN_NOT_NULL = """
- name: Example task
  debug:
    msg: test
  when: my_var not None
"""

FAIL_LITERAL_TRUE = """
- name: Example task
  debug:
    msg: test
  when: my_var == True
"""

FAIL_LITERAL_FALSE = """
- name: Example task
  debug:
    msg: test
  when: my_var == false

- name: Another example task
  debug:
    msg: test
  when:
    - my_var == false
"""


@pytest.mark.parametrize(
    ("input_str", "found_errors"),
    (
        pytest.param(
            PASS_WHEN,
            0,
            id="pass_when",
        ),
        pytest.param(
            PASS_WHEN_NOT_FALSE,
            0,
            id="when_not_false",
        ),
        pytest.param(
            PASS_WHEN_NOT_NULL,
            0,
            id="when_not_null",
        ),
        pytest.param(
            FAIL_LITERAL_TRUE,
            1,
            id="literal_true",
        ),
        pytest.param(
            FAIL_LITERAL_FALSE,
            2,
            id="literal_false",
        ),
    ),
)
def test_literal_compare(input_str: str, found_errors: int) -> None:
    """Test literal-compare."""
    collection = RulesCollection()
    collection.register(ComparisonToLiteralBoolRule())
    runner = RunFromText(collection)
    results = runner.run_role_tasks_main(input_str)
    assert len(results) == found_errors
