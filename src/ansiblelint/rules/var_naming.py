"""Implementation of var-naming rule."""
from __future__ import annotations

import keyword
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ansible.parsing.yaml.objects import AnsibleUnicode

from ansiblelint.config import options
from ansiblelint.constants import LINE_NUMBER_KEY, RC
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.utils import Task


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


class VariableNamingRule(AnsibleLintRule):
    """All variables should be named using only lowercase and underscores."""

    id = "var-naming"
    severity = "MEDIUM"
    tags = ["idiom"]
    version_added = "v5.0.10"
    needs_raw_task = True

    def is_invalid_variable_name(self, ident: str, role_ident: str = "") -> bool:
        """Check if variable name is using right pattern."""
        # Based on https://github.com/ansible/ansible/blob/devel/lib/ansible/utils/vars.py#L235
        if not ident.startswith("__"):
            var_naming_pattern = options.var_naming_pattern or "^[a-z_][a-z0-9_]*$"
            re_pattern = re.compile(
                var_naming_pattern.format(role=role_ident),
            )
        else:
            re_pattern = re.compile("^[a-z_][a-z0-9_]*$")

        if not isinstance(ident, str):  # pragma: no cover
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
        return not bool(re_pattern.match(ident))

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific playbook."""
        results: list[MatchError] = []
        raw_results: list[MatchError] = []

        if not data or file.kind not in ("tasks", "handlers", "playbook", "vars"):
            return results
        # If the Play uses the 'vars' section to set variables
        our_vars = data.get("vars", {})
        for key in our_vars:
            if self.is_invalid_variable_name(key):
                raw_results.append(
                    self.create_matcherror(
                        filename=file,
                        lineno=key.ansible_pos[1]
                        if isinstance(key, AnsibleUnicode)
                        else our_vars[LINE_NUMBER_KEY],
                        message="Play defines variable '"
                        + key
                        + "' within 'vars' section that violates variable naming standards",
                        tag=f"var-naming[{key}]",
                    ),
                )
        if raw_results:
            lines = file.content.splitlines()
            for match in raw_results:
                # lineno starts with 1, not zero
                skip_list = get_rule_skips_from_line(
                    line=lines[match.lineno - 1],
                    lintable=file,
                )
                if match.rule.id not in skip_list and match.tag not in skip_list:
                    results.append(match)

        return results

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        """Return matches for task based variables."""
        results = []
        role_name = ""
        # If the task uses the 'vars' section to set variables
        split_filepath = (
            Path(str(task.get("__file__"))).resolve().as_posix().split("roles/")
        )
        if len(split_filepath) > 1 and task["action"]["__ansible_module__"] not in [
            "import_tasks",
            "include_tasks",
            "import_role",
            "include_role",
        ]:
            role_name = split_filepath[1].split("/")[0]
        our_vars = task.get("vars", {})
        for key in our_vars:
            if self.is_invalid_variable_name(key, role_ident=role_name):
                results.append(
                    self.create_matcherror(
                        filename=file,
                        lineno=our_vars[LINE_NUMBER_KEY],
                        message=f"Task defines variable within 'vars' section that violates variable naming standards: {key}",
                        tag=f"var-naming[{key}]",
                    ),
                )

        # If the task uses the 'set_fact' module
        ansible_module = task["action"]["__ansible_module__"]
        if ansible_module == "set_fact":
            for key in filter(
                lambda x: isinstance(x, str) and not x.startswith("__"),
                task["action"].keys(),
            ):
                if self.is_invalid_variable_name(key, role_ident=role_name):
                    results.append(
                        self.create_matcherror(
                            filename=file,
                            lineno=task["action"][LINE_NUMBER_KEY],
                            message=f"Task uses 'set_fact' to define variables that violates variable naming standards: {key}",
                            tag=f"var-naming[{key}]",
                        ),
                    )

        # If the task registers a variable
        registered_var = task.get("register", None)
        if registered_var and self.is_invalid_variable_name(
            registered_var,
            role_ident=role_name,
        ):
            results.append(
                self.create_matcherror(
                    filename=file,
                    lineno=task[LINE_NUMBER_KEY],
                    message=f"Task registers a variable that violates variable naming standards: {registered_var}",
                    tag=f"var-naming[{registered_var}]",
                ),
            )

        return results

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches for variables defined in vars files."""
        results: list[MatchError] = []
        raw_results: list[MatchError] = []
        meta_data: dict[AnsibleUnicode, Any] = {}
        role_name = ""

        if str(file.kind) == "vars" and file.data:
            split_filepath = str(file.data.get("__file__").absolute()).split("roles/")
            if len(split_filepath) > 1:
                role_name = split_filepath[1].split("/")[0]
            meta_data = parse_yaml_from_file(str(file.path))
            for key in meta_data:
                if self.is_invalid_variable_name(key, role_ident=role_name):
                    raw_results.append(
                        self.create_matcherror(
                            filename=file,
                            lineno=key.ansible_pos[1],
                            message="File defines variable '"
                            + key
                            + "' that violates variable naming standards",
                        ),
                    )
            if raw_results:
                lines = file.content.splitlines()
                for match in raw_results:
                    # lineno starts with 1, not zero
                    skip_list = get_rule_skips_from_line(
                        line=lines[match.lineno - 1],
                        lintable=file,
                    )
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
        ("file", "expected"),
        (
            pytest.param("examples/playbooks/rule-var-naming-fail.yml", 7, id="0"),
            pytest.param("examples/Taskfile.yml", 0, id="1"),
        ),
    )
    def test_invalid_var_name_playbook(file: str, expected: int) -> None:
        """Test rule matches."""
        rules = RulesCollection(options=options)
        rules.register(VariableNamingRule())
        results = Runner(Lintable(file), rules=rules).run()
        assert len(results) == expected
        for result in results:
            assert result.rule.id == VariableNamingRule.id
        # We are not checking line numbers because they can vary between
        # different versions of ruamel.yaml (and depending on presence/absence
        # of its c-extension)

    @pytest.mark.parametrize(
        "rule_runner",
        (VariableNamingRule,),
        indirect=["rule_runner"],
    )
    def test_invalid_var_name_varsfile(
        rule_runner: RunFromText,
        tmp_path: Path,
    ) -> None:
        """Test rule matches."""
        results = rule_runner.run_role_defaults_main(FAIL_VARS, tmp_path=tmp_path)
        assert len(results) == 2
        for result in results:
            assert result.rule.id == VariableNamingRule.id

        # list unexpected error lines or non-matching error lines
        expected_error_lines = [2, 6]
        lines = [i.lineno for i in results]
        error_lines_difference = list(
            set(expected_error_lines).symmetric_difference(set(lines)),
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
        assert result.returncode == RC.SUCCESS
        assert "var-naming" not in result.stdout

    def test_is_invalid_variable_name() -> None:
        """Test for invalid variable names."""
        var_name_rule = VariableNamingRule()
        assert var_name_rule.is_invalid_variable_name("assert") is False
        assert var_name_rule.is_invalid_variable_name("é") is False
