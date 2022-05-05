"""Implementation of var-naming rule."""
import keyword
import re
import sys
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ansible.parsing.yaml.objects import AnsibleUnicode

from ansiblelint.config import options
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.utils import LINE_NUMBER_KEY, parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.constants import odict
    from ansiblelint.errors import MatchError


# Should raise var-naming at line [4, 8, 18, 20].
FAIL_PLAY = """---
- hosts: localhost
  vars:
    CamelCaseIsBad: false  # invalid
    this_is_valid:  # valid because content is a dict, not a variable
      CamelCase: ...
      ALL_CAPS: ...
    ALL_CAPS_ARE_BAD_TOO: ...  # invalid
    CamelCaseButErrorIgnored: true  # noqa: var-naming

  tasks:
    - name: foo
      ansible.builtin.set_fact:
        "{{ 'test_' }}var": "value"  # valid
    - name: bar
      ansible.builtin.set_fact:
        CamelCaseButErrorIgnored: true  # noqa: var-naming
    - name: test in a block
      block:
        - name:
          ansible.builtin.set_fact:
            CamelCaseIsBad: "{{ BAD }}" # invalid
          vars:
            ALL_CAPS_ARE_BAD_TOO: "{{ MoreBad }}" # invalid
      vars:
        BAD: false # invalid
        MoreBad: ... # invalid
"""


# Should raise var-naming at line [2, 6].
FAIL_VARS = """---
CamelCaseIsBad: false  # invalid
this_is_valid:  # valid because content is a dict, not a variable
  CamelCase: ...
  ALL_CAPS: ...
ALL_CAPS_ARE_BAD_TOO: ...  # invalid
"{{ 'test_' }}var": "value"  # valid
CamelCaseButErrorIgnored: true  # noqa: var-naming
"""


# properties/parameters are prefixed and postfixed with `__`
def is_property(k: str) -> bool:
    """Check if key is a property."""
    return k.startswith("__") and k.endswith("__")


class VariableNamingRule(AnsibleLintRule):
    """All variables should be named using only lowercase and underscores."""

    id = "var-naming"
    severity = "MEDIUM"
    tags = ["idiom", "experimental"]
    version_added = "v5.0.10"
    re_pattern = re.compile(options.var_naming_pattern or "^[a-z_][a-z0-9_]*$")

    def is_invalid_variable_name(self, ident: str) -> bool:
        """Check if variable name is using right pattern."""
        # Based on https://github.com/ansible/ansible/blob/devel/lib/ansible/utils/vars.py#L235
        if not isinstance(ident, str):
            return False

        try:
            ident.encode("ascii")
        except UnicodeEncodeError:
            return False

        if keyword.iskeyword(ident):
            return False

        # We want to allow use of jinja2 templating for variable names
        if "{{" in ident:
            return False

        # previous tests should not be triggered as they would have raised a
        # syntax-error when we loaded the files but we keep them here as a
        # safety measure.
        return not bool(self.re_pattern.match(ident))

    def matchplay(
        self, file: "Lintable", data: "odict[str, Any]"
    ) -> List["MatchError"]:
        """Return matches found for a specific playbook."""
        results: List["MatchError"] = []
        raw_results: List["MatchError"] = []

        # If the Play uses the 'vars' section to set variables
        our_vars = data.get("vars", {})
        for key in our_vars.keys():
            if self.is_invalid_variable_name(key):
                raw_results.append(
                    self.create_matcherror(
                        filename=file,
                        linenumber=key.ansible_pos[1]
                        if isinstance(key, AnsibleUnicode)
                        else our_vars[LINE_NUMBER_KEY],
                        message="Play defines variable '"
                        + key
                        + "' within 'vars' section that violates variable naming standards",
                    )
                )
        if raw_results:
            lines = file.content.splitlines()
            for match in raw_results:
                # linenumber starts with 1, not zero
                skip_list = get_rule_skips_from_line(lines[match.linenumber - 1])
                if match.rule.id not in skip_list and match.tag not in skip_list:
                    results.append(match)

        return results

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        """Return matches for task based variables."""
        # If the task uses the 'vars' section to set variables
        our_vars = task.get("vars", {})
        for key in our_vars.keys():
            if self.is_invalid_variable_name(key):
                return "Task defines variables within 'vars' section that violates variable naming standards"

        # If the task uses the 'set_fact' module
        ansible_module = task["action"]["__ansible_module__"]
        ansible_action = task["action"]
        if ansible_module == "set_fact":
            for key in ansible_action.keys():
                if self.is_invalid_variable_name(key):
                    return "Task uses 'set_fact' to define variables that violates variable naming standards"

        # If the task registers a variable
        registered_var = task.get("register", None)
        if registered_var and self.is_invalid_variable_name(registered_var):
            return "Task registers a variable that violates variable naming standards"

        return False

    def matchyaml(self, file: Lintable) -> List["MatchError"]:
        """Return matches for variables defined in vars files."""
        results: List["MatchError"] = []
        raw_results: List["MatchError"] = []
        meta_data: Dict[AnsibleUnicode, Any] = {}

        if str(file.kind) == "vars":
            meta_data = parse_yaml_from_file(str(file.path))
            for key in meta_data.keys():
                if self.is_invalid_variable_name(key):
                    raw_results.append(
                        self.create_matcherror(
                            filename=file,
                            linenumber=key.ansible_pos[1],
                            message="File defines variable '"
                            + key
                            + "' that violates variable naming standards",
                        )
                    )
            if raw_results:
                lines = file.content.splitlines()
                for match in raw_results:
                    # linenumber starts with 1, not zero
                    skip_list = get_rule_skips_from_line(lines[match.linenumber - 1])
                    if match.rule.id not in skip_list and match.tag not in skip_list:
                        results.append(match)
        else:
            results.extend(super().matchyaml(file))
        return results


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        "rule_runner", (VariableNamingRule,), indirect=["rule_runner"]
    )
    def test_invalid_var_name_playbook(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_playbook(FAIL_PLAY)
        assert len(results) == 4
        for result in results:
            assert result.rule.id == VariableNamingRule.id

        # list unexpected error lines or non-matching error lines
        expected_error_lines = [4, 8, 18, 20]
        lines = [i.linenumber for i in results]
        error_lines_difference = list(
            set(expected_error_lines).symmetric_difference(set(lines))
        )
        assert len(error_lines_difference) == 0

    @pytest.mark.parametrize(
        "rule_runner", (VariableNamingRule,), indirect=["rule_runner"]
    )
    def test_invalid_var_name_varsfile(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run_role_defaults_main(FAIL_VARS)
        assert len(results) == 2
        for result in results:
            assert result.rule.id == VariableNamingRule.id

        # list unexpected error lines or non-matching error lines
        expected_error_lines = [2, 6]
        lines = [i.linenumber for i in results]
        error_lines_difference = list(
            set(expected_error_lines).symmetric_difference(set(lines))
        )
        assert len(error_lines_difference) == 0
