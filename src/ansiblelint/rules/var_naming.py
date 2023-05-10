"""Implementation of var-naming rule."""
from __future__ import annotations

import keyword
import re
import sys
from typing import TYPE_CHECKING, Any

from ansible.parsing.yaml.objects import AnsibleUnicode

from ansiblelint.config import options
from ansiblelint.constants import LINE_NUMBER_KEY, RC
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.utils import Task


class VariableNamingRule(AnsibleLintRule):
    """All variables should be named using only lowercase and underscores."""

    id = "var-naming"
    severity = "MEDIUM"
    tags = ["idiom"]
    version_added = "v5.0.10"
    needs_raw_task = True
    re_pattern_str = options.var_naming_pattern or "^[a-z_][a-z0-9_]*$"
    re_pattern = re.compile(re_pattern_str)

    # pylint: disable=too-many-return-statements)
    def get_var_naming_matcherror(
        self,
        ident: str,
        *,
        prefix: str = "",
    ) -> MatchError | None:
        """Return a MatchError if the variable name is not valid, otherwise None."""
        if not isinstance(ident, str):  # pragma: no cover
            return MatchError(
                tag="var-naming[non-string]",
                message="Variables names must be strings.",
                rule=self,
            )

        try:
            ident.encode("ascii")
        except UnicodeEncodeError:
            return MatchError(
                tag="var-naming[non-ascii]",
                message="Variables names must be ASCII.",
                rule=self,
            )

        if keyword.iskeyword(ident):
            return MatchError(
                tag="var-naming[no-keyword]",
                message="Variables names must not be Python keywords.",
                rule=self,
            )

        # We want to allow use of jinja2 templating for variable names
        if "{{" in ident:
            return MatchError(
                tag="var-naming[no-jinja]",
                message="Variables names must not contain jinja2 templating.",
                rule=self,
            )

        if not bool(self.re_pattern.match(ident)):
            return MatchError(
                tag="var-naming[pattern]",
                message=f"Variables names should match {self.re_pattern_str} regex.",
                rule=self,
            )

        if prefix and not ident.startswith(f"{prefix}_"):
            return MatchError(
                tag="var-naming[no-role-prefix]",
                message="Variables names from within roles should use role_name_ as a prefix.",
                rule=self,
            )
        return None

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific playbook."""
        results: list[MatchError] = []
        raw_results: list[MatchError] = []

        if not data or file.kind not in ("tasks", "handlers", "playbook", "vars"):
            return results
        # If the Play uses the 'vars' section to set variables
        our_vars = data.get("vars", {})
        for key in our_vars:
            match_error = self.get_var_naming_matcherror(key)
            if match_error:
                match_error.filename = str(file.path)
                match_error.lineno = (
                    key.ansible_pos[1]
                    if isinstance(key, AnsibleUnicode)
                    else our_vars[LINE_NUMBER_KEY]
                )
                raw_results.append(match_error)
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
        prefix = ""
        filename = "" if file is None else str(file.path)
        if file and file.parent and file.parent.kind == "role":
            prefix = file.parent.path.name
        # If the task uses the 'vars' section to set variables
        our_vars = task.get("vars", {})
        for key in our_vars:
            match_error = self.get_var_naming_matcherror(key, prefix=prefix)
            if match_error:
                match_error.filename = filename
                match_error.lineno = our_vars[LINE_NUMBER_KEY]
                match_error.message += f" (vars: {key})"
                results.append(match_error)

        # If the task uses the 'set_fact' module
        # breakpoint()
        ansible_module = task["action"]["__ansible_module__"]
        if ansible_module == "set_fact":
            for key in filter(
                lambda x: isinstance(x, str) and not x.startswith("__"),
                task["action"].keys(),
            ):
                match_error = self.get_var_naming_matcherror(key, prefix=prefix)
                if match_error:
                    match_error.filename = filename
                    match_error.lineno = task["action"][LINE_NUMBER_KEY]
                    match_error.message += f" (set_fact: {key})"
                    results.append(match_error)

        # If the task registers a variable
        registered_var = task.get("register", None)
        if registered_var:
            match_error = self.get_var_naming_matcherror(registered_var, prefix=prefix)
            if match_error:
                match_error.message += f" (register: {registered_var})"
                match_error.filename = filename
                match_error.lineno = task[LINE_NUMBER_KEY]
                results.append(match_error)

        return results

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches for variables defined in vars files."""
        results: list[MatchError] = []
        raw_results: list[MatchError] = []
        meta_data: dict[AnsibleUnicode, Any] = {}
        filename = "" if file is None else str(file.path)

        if str(file.kind) == "vars" and file.data:
            meta_data = parse_yaml_from_file(str(file.path))
            for key in meta_data:
                match_error = self.get_var_naming_matcherror(key)
                if match_error:
                    match_error.filename = filename
                    match_error.lineno = key.ansible_pos[1]
                    match_error.message += f" (vars: {key})"
                    raw_results.append(match_error)
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

    def test_invalid_var_name_varsfile(
        default_rules_collection: RulesCollection,
    ) -> None:
        """Test rule matches."""
        results = Runner(
            Lintable("examples/playbooks/vars/rule_var_naming_fail.yml"),
            rules=default_rules_collection,
        ).run()
        expected_errors = (
            ("schema[vars]", 1),
            ("var-naming[pattern]", 2),
            ("var-naming[pattern]", 6),
            ("var-naming[no-jinja]", 7),
            ("var-naming[no-keyword]", 9),
            ("var-naming[non-ascii]", 10),
        )
        assert len(results) == len(expected_errors)
        for idx, result in enumerate(results):
            assert result.tag == expected_errors[idx][0]
            assert result.lineno == expected_errors[idx][1]

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
