"""Implementation of var-naming rule."""

from __future__ import annotations

import keyword
import re
import sys
from typing import TYPE_CHECKING, Any

from ansible.parsing.yaml.objects import AnsibleUnicode
from ansible.vars.reserved import get_reserved_names

from ansiblelint.config import Options, options
from ansiblelint.constants import (
    ANNOTATION_KEYS,
    LINE_NUMBER_KEY,
    PLAYBOOK_ROLE_KEYWORDS,
    RC,
)
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.text import has_jinja, is_fqcn_or_name
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
    reserved_names = get_reserved_names()
    # List of special variables that should be treated as read-only. This list
    # does not include connection variables, which we expect users to tune in
    # specific cases.
    # https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html
    read_only_names = {
        "ansible_check_mode",
        "ansible_collection_name",
        "ansible_config_file",
        "ansible_dependent_role_names",
        "ansible_diff_mode",
        "ansible_forks",
        "ansible_index_var",
        "ansible_inventory_sources",
        "ansible_limit",
        "ansible_local",  # special fact
        "ansible_loop",
        "ansible_loop_var",
        "ansible_parent_role_names",
        "ansible_parent_role_paths",
        "ansible_play_batch",
        "ansible_play_hosts",
        "ansible_play_hosts_all",
        "ansible_play_name",
        "ansible_play_role_names",
        "ansible_playbook_python",
        "ansible_role_name",
        "ansible_role_names",
        "ansible_run_tags",
        "ansible_search_path",
        "ansible_skip_tags",
        "ansible_verbosity",
        "ansible_version",
        "group_names",
        "groups",
        "hostvars",
        "inventory_dir",
        "inventory_file",
        "inventory_hostname",
        "inventory_hostname_short",
        "omit",
        "play_hosts",
        "playbook_dir",
        "role_name",
        "role_names",
        "role_path",
    }

    # These special variables are used by Ansible but we allow users to set
    # them as they might need it in certain cases.
    allowed_special_names = {
        "ansible_facts",
        "ansible_become_user",
        "ansible_connection",
        "ansible_host",
        "ansible_python_interpreter",
        "ansible_user",
        "ansible_remote_tmp",  # no included in docs
    }
    _ids = {
        "var-naming[no-reserved]": "Variables names must not be Ansible reserved names.",
        "var-naming[no-jinja]": "Variables names must not contain jinja2 templating.",
        "var-naming[pattern]": f"Variables names should match {re_pattern_str} regex.",
    }

    # pylint: disable=too-many-return-statements
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

        if ident in ANNOTATION_KEYS or ident in self.allowed_special_names:
            return None

        try:
            ident.encode("ascii")
        except UnicodeEncodeError:
            return MatchError(
                tag="var-naming[non-ascii]",
                message=f"Variables names must be ASCII. ({ident})",
                rule=self,
            )

        if keyword.iskeyword(ident):
            return MatchError(
                tag="var-naming[no-keyword]",
                message=f"Variables names must not be Python keywords. ({ident})",
                rule=self,
            )

        if ident in self.reserved_names:
            return MatchError(
                tag="var-naming[no-reserved]",
                message=f"Variables names must not be Ansible reserved names. ({ident})",
                rule=self,
            )

        if ident in self.read_only_names:
            return MatchError(
                tag="var-naming[read-only]",
                message=f"This special variable is read-only. ({ident})",
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
                message=f"Variables names should match {self.re_pattern_str} regex. ({ident})",
                rule=self,
            )

        if (
            prefix
            and not ident.lstrip("_").startswith(f"{prefix}_")
            and not has_jinja(prefix)
            and is_fqcn_or_name(prefix)
        ):
            return MatchError(
                tag="var-naming[no-role-prefix]",
                message=f"Variables names from within roles should use {prefix}_ as a prefix.",
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
        roles = data.get("roles", [])
        for role in roles:
            if isinstance(role, AnsibleUnicode):
                continue
            role_fqcn = role.get("role", role.get("name"))
            prefix = role_fqcn.split("/" if "/" in role_fqcn else ".")[-1]
            for key in list(role.keys()):
                if key not in PLAYBOOK_ROLE_KEYWORDS:
                    match_error = self.get_var_naming_matcherror(key, prefix=prefix)
                    if match_error:
                        match_error.filename = str(file.path)
                        match_error.message += f" (vars: {key})"
                        match_error.lineno = (
                            key.ansible_pos[1]
                            if isinstance(key, AnsibleUnicode)
                            else role[LINE_NUMBER_KEY]
                        )
                        raw_results.append(match_error)

            our_vars = role.get("vars", {})
            for key in our_vars:
                match_error = self.get_var_naming_matcherror(key, prefix=prefix)
                if match_error:
                    match_error.filename = str(file.path)
                    match_error.message += f" (vars: {key})"
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
        ansible_module = task["action"]["__ansible_module__"]
        # If the task uses the 'vars' section to set variables
        our_vars = task.get("vars", {})
        if ansible_module in ("include_role", "import_role"):
            action = task["action"]
            if isinstance(action, dict):
                role_fqcn = action.get("name", "")
                prefix = role_fqcn.split("/" if "/" in role_fqcn else ".")[-1]
        else:
            prefix = ""
        for key in our_vars:
            match_error = self.get_var_naming_matcherror(key, prefix=prefix)
            if match_error:
                match_error.filename = filename
                match_error.lineno = our_vars[LINE_NUMBER_KEY]
                match_error.message += f" (vars: {key})"
                results.append(match_error)

        # If the task uses the 'set_fact' module
        if ansible_module == "set_fact":
            for key in filter(
                lambda x: isinstance(x, str)
                and not x.startswith("__")
                and x != "cacheable",
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
                prefix = file.role if file.role else ""
                match_error = self.get_var_naming_matcherror(key, prefix=prefix)
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
            pytest.param(
                "examples/playbooks/var-naming/rule-var-naming-fail.yml",
                7,
                id="0",
            ),
            pytest.param("examples/Taskfile.yml", 0, id="1"),
        ),
    )
    def test_invalid_var_name_playbook(
        file: str,
        expected: int,
        config_options: Options,
    ) -> None:
        """Test rule matches."""
        rules = RulesCollection(options=config_options)
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
            ("var-naming[no-reserved]", 11),
            ("var-naming[read-only]", 12),
        )
        assert len(results) == len(expected_errors)
        for idx, result in enumerate(results):
            assert result.tag == expected_errors[idx][0]
            assert result.lineno == expected_errors[idx][1]

    def test_var_naming_with_role_prefix(
        default_rules_collection: RulesCollection,
    ) -> None:
        """Test rule matches."""
        results = Runner(
            Lintable("examples/roles/role_vars_prefix_detection"),
            rules=default_rules_collection,
        ).run()
        assert len(results) == 2
        for result in results:
            assert result.tag == "var-naming[no-role-prefix]"

    def test_var_naming_with_role_prefix_plays(
        default_rules_collection: RulesCollection,
    ) -> None:
        """Test rule matches."""
        results = Runner(
            Lintable("examples/playbooks/role_vars_prefix_detection.yml"),
            rules=default_rules_collection,
            exclude_paths=["examples/roles/role_vars_prefix_detection"],
        ).run()
        expected_errors = (
            ("var-naming[no-role-prefix]", 9),
            ("var-naming[no-role-prefix]", 12),
            ("var-naming[no-role-prefix]", 15),
            ("var-naming[no-role-prefix]", 25),
            ("var-naming[no-role-prefix]", 32),
            ("var-naming[no-role-prefix]", 45),
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

    def test_var_naming_with_include_tasks_and_vars() -> None:
        """Test with include tasks and vars."""
        role_path = "examples/roles/var_naming_pattern/tasks/include_task_with_vars.yml"
        result = run_ansible_lint(role_path)
        assert result.returncode == RC.SUCCESS
        assert "var-naming" not in result.stdout

    def test_var_naming_with_set_fact_and_cacheable() -> None:
        """Test with include tasks and vars."""
        role_path = "examples/roles/var_naming_pattern/tasks/cacheable_set_fact.yml"
        result = run_ansible_lint(role_path)
        assert result.returncode == RC.SUCCESS
        assert "var-naming" not in result.stdout

    def test_var_naming_with_include_role_import_role() -> None:
        """Test with include role and import role."""
        role_path = "examples/.test_collection/roles/my_role/tasks/main.yml"
        result = run_ansible_lint(role_path)
        assert result.returncode == RC.SUCCESS
        assert "var-naming" not in result.stdout
