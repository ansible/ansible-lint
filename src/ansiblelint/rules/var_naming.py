"""Implementation of var-naming rule."""
from __future__ import annotations

import keyword
import re
import sys
from typing import TYPE_CHECKING, Any

from ansible.parsing.yaml.objects import AnsibleUnicode

from ansiblelint.config import options
from ansiblelint.constants import LINE_NUMBER_KEY, SUCCESS_RC
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError

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
    needs_raw_task = True
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

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific playbook."""
        results: list[MatchError] = []
        raw_results: list[MatchError] = []

        if not data:
            return results
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
                        tag=f"var-naming[{key}]",
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
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> list[MatchError]:
        """Return matches for task based variables."""
        results = []
        # If the task uses the 'vars' section to set variables
        our_vars = task.get("vars", {})
        for key in our_vars.keys():
            if self.is_invalid_variable_name(key):
                results.append(
                    self.create_matcherror(
                        filename=file,
                        linenumber=our_vars[LINE_NUMBER_KEY],
                        message=f"Task defines variable within 'vars' section that violates variable naming standards: {key}",
                        tag=f"var-naming[{key}]",
                    )
                )

        # If the task uses the 'set_fact' module
        ansible_module = task["action"]["__ansible_module__"]
        if ansible_module == "set_fact":
            for key in filter(
                lambda x: isinstance(x, str) and not x.startswith("__"),
                task["action"].keys(),
            ):
                if self.is_invalid_variable_name(key):
                    results.append(
                        self.create_matcherror(
                            filename=file,
                            linenumber=task["action"][LINE_NUMBER_KEY],
                            message=f"Task uses 'set_fact' to define variables that violates variable naming standards: {key}",
                            tag=f"var-naming[{key}]",
                        )
                    )

        # If the task registers a variable
        registered_var = task.get("register", None)
        if registered_var and self.is_invalid_variable_name(registered_var):
            results.append(
                self.create_matcherror(
                    filename=file,
                    linenumber=0,
                    message=f"Task registers a variable that violates variable naming standards: {registered_var}",
                    tag=f"var-naming[{registered_var}]",
                )
            )

        return results

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches for variables defined in vars files."""
        results: list[MatchError] = []
        raw_results: list[MatchError] = []
        meta_data: dict[AnsibleUnicode, Any] = {}

        if str(file.kind) == "vars" and file.data:
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

    from ansiblelint.testing import (  # pylint: disable=ungrouped-imports
        RunFromText,
        run_ansible_lint,
    )

    @pytest.mark.parametrize(
        "rule_runner", (VariableNamingRule,), indirect=["rule_runner"]
    )
    def test_invalid_var_name_playbook(rule_runner: RunFromText) -> None:
        """Test rule matches."""
        results = rule_runner.run("examples/playbooks/rule-var-naming-fail.yml")
        assert len(results) == 6
        for result in results:
            assert result.rule.id == VariableNamingRule.id
        # We are not checking line numbers because they can vary between
        # different versions of ruamel.yaml (and depending on presence/absence
        # of its c-extension)

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

    def test_var_naming_with_pattern() -> None:
        """Test rule matches."""
        role_path = "examples/roles/var_naming_pattern/tasks/main.yml"
        conf_path = "examples/roles/var_naming_pattern/.ansible-lint"
        result = run_ansible_lint(
            f"--config-file={conf_path}",
            role_path,
        )
        assert result.returncode == SUCCESS_RC
        assert "var-naming" not in result.stdout
