"""Implementation of var-naming rule."""

from __future__ import annotations

import keyword
import re
import sys
from typing import TYPE_CHECKING, Any, NamedTuple

from ansible.vars.reserved import get_reserved_names

from ansiblelint.config import Options, options
from ansiblelint.constants import (
    ANNOTATION_KEYS,
    PLAYBOOK_ROLE_KEYWORDS,
    RC,
)
from ansiblelint.file_utils import Lintable, find_role_dir
from ansiblelint.rules import AnsibleLintRule, RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.text import has_jinja, is_fqcn, is_fqcn_or_name
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.app import App
    from ansiblelint.errors import MatchError
    from ansiblelint.utils import Task


class Prefix(NamedTuple):
    """Prefix."""

    value: str = ""
    from_fqcn: bool = False
    # Name for which no usable prefix could be derived, empty when the prefix
    # was determined successfully.
    unknown: str = ""


class VariableNamingRule(AnsibleLintRule):
    """All variables should be named using only lowercase and underscores."""

    id = "var-naming"
    severity = "MEDIUM"
    tags = ["idiom"]
    version_changed = "5.0.10"
    needs_raw_task = True
    re_pattern_str = options.var_naming_pattern or "^[a-z_][a-z0-9_]*$"
    re_pattern = re.compile(re_pattern_str)
    reserved_names = get_reserved_names()
    # List of special variables that should be treated as read-only. This list
    # does not include connection variables, which we expect users to tune in
    # specific cases.
    # https://docs.ansible.com/projects/ansible/latest/reference_appendices/special_variables.html
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
        prefix: Prefix | None = None,
        file: Lintable,
    ) -> MatchError | None:
        """Return a MatchError if the variable name is not valid, otherwise None."""
        if not isinstance(ident, str):  # pragma: no cover
            return self.create_matcherror(
                tag="var-naming[non-string]",
                message="Variables names must be strings.",
                filename=file,
            )

        if ident in ANNOTATION_KEYS or ident in self.allowed_special_names:
            return None

        try:
            ident.encode("ascii")
        except UnicodeEncodeError:
            return self.create_matcherror(
                tag="var-naming[non-ascii]",
                message=f"Variables names must be ASCII. ({ident})",
                filename=file,
                data=ident,
            )

        if keyword.iskeyword(ident):
            return self.create_matcherror(
                tag="var-naming[no-keyword]",
                message=f"Variables names must not be Python keywords. ({ident})",
                filename=file,
                data=ident,
            )

        if ident in self.reserved_names:
            return self.create_matcherror(
                tag="var-naming[no-reserved]",
                message=f"Variables names must not be Ansible reserved names. ({ident})",
                filename=file,
                data=ident,
            )

        if ident in self.read_only_names:
            return self.create_matcherror(
                tag="var-naming[read-only]",
                message=f"This special variable is read-only. ({ident})",
                filename=file,
                data=ident,
            )

        # We want to allow use of jinja2 templating for variable names
        if "{{" in ident:
            return None

        if not bool(self.re_pattern.match(ident)) and (
            not prefix or not prefix.from_fqcn
        ):
            return self.create_matcherror(
                tag="var-naming[pattern]",
                message=f"Variables names should match {self.re_pattern_str} regex. ({ident})",
                filename=file,
                data=ident,
            )

        # A role prefix we could not determine must not silently skip the
        # check, report the offending role name instead.
        if prefix and prefix.unknown and not ident.lstrip("_").startswith("ansible_"):
            return self.create_matcherror(
                tag="var-naming[no-role-prefix]",
                message=(
                    "Variables names from within roles should use the role name "
                    f"as a prefix, which could not be determined for '{prefix.unknown}'."
                ),
                filename=file,
                data=ident,
            )

        # Variables in the ansible_ namespace are owned by Ansible itself
        # (connection variables like ansible_ssh_common_args, ansible_port, ...)
        # and cannot be renamed to carry a role prefix.
        if (
            prefix
            and not ident.lstrip("_").startswith("ansible_")
            and not ident.lstrip("_").startswith(f"{prefix.value}_")
            and not has_jinja(prefix.value)
            and is_fqcn_or_name(prefix.value)
        ):
            return self.create_matcherror(
                tag="var-naming[no-role-prefix]",
                message=f"Variables names from within roles should use {prefix.value}_ as a prefix.",
                filename=file,
                data=ident,
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
            match_error = self.get_var_naming_matcherror(key, file=file)
            if match_error:
                raw_results.append(match_error)
        roles = data.get("roles", [])
        for role in roles:
            if isinstance(role, str):
                continue
            role_fqcn = role.get("role", role.get("name"))
            prefix = self._parse_prefix(role_fqcn)
            for key in role:
                if key not in PLAYBOOK_ROLE_KEYWORDS:
                    match_error = self.get_var_naming_matcherror(
                        key, prefix=prefix, file=file
                    )
                    if match_error:
                        match_error.message += f" (vars: {key})"
                        raw_results.append(match_error)

            our_vars = role.get("vars", {})
            for key in our_vars:
                match_error = self.get_var_naming_matcherror(
                    key,
                    prefix=prefix,
                    file=file,
                )
                if match_error:
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

        return results

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> list[MatchError]:
        """Return matches for task based variables."""
        results = []
        task_prefix = Prefix()
        role_prefix = Prefix()
        if file:
            role_prefix = self._get_role_prefix(file)
        ansible_module = task["action"]["__ansible_module__"]
        # If the task uses the 'vars' section to set variables
        # only check role prefix for include_role and import_role tasks 'vars'
        our_vars = task.get("vars", {})
        if ansible_module in ("include_role", "import_role"):
            action = task["action"]
            if isinstance(action, dict):
                role_fqcn = action.get("name", "")
                task_prefix = self._parse_prefix(role_fqcn)
        for key in our_vars:
            match_error = self.get_var_naming_matcherror(
                key,
                prefix=task_prefix,
                file=file or Lintable(""),
            )
            if match_error:
                match_error.message += f" (vars: {key})"
                results.append(match_error)

        # If the task uses the 'set_fact' module
        if ansible_module == "set_fact":
            for key in filter(
                lambda x: (
                    isinstance(x, str) and not x.startswith("__") and x != "cacheable"
                ),
                task["action"].keys(),
            ):
                match_error = self.get_var_naming_matcherror(
                    key,
                    prefix=role_prefix,
                    file=file or Lintable(""),
                )
                if match_error:
                    match_error.lineno = task.line
                    match_error.message += f" (set_fact: {key})"
                    results.append(match_error)

        # If the task registers a variable
        registered_var = task.get("register", None)
        if registered_var:
            registered_vars = (
                registered_var.keys()
                if isinstance(registered_var, dict)
                else (registered_var,)
            )
            for key in registered_vars:
                if isinstance(key, str) and key.startswith("__"):
                    continue
                match_error = self.get_var_naming_matcherror(
                    key,
                    prefix=role_prefix,
                    file=file or Lintable(""),
                )
                if match_error:
                    match_error.message += f" (register: {key})"
                    match_error.lineno = task.line
                    results.append(match_error)

        return results

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches for variables defined in vars files."""
        results: list[MatchError] = []
        raw_results: list[MatchError] = []

        if str(file.kind) == "vars" and file.data:
            meta_data = parse_yaml_from_file(str(file.path))
            if not isinstance(meta_data, dict):
                msg = f"Content if vars file {file} is not a dictionary."
                raise TypeError(msg)
            prefix = self._get_role_prefix(file)
            for key in meta_data:
                match_error = self.get_var_naming_matcherror(
                    key,
                    prefix=prefix,
                    file=file,
                )
                if match_error:
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

    @staticmethod
    def _get_role_prefix(file: Lintable) -> Prefix:
        """Return the variable prefix expected inside the role containing file."""
        if not file.role:
            return Prefix()
        if "." not in file.role:
            return Prefix(file.role)
        # A dotted role directory is a Galaxy 'namespace.role' install: prefer
        # the role_name declared in meta/main.yml, else use the part of the
        # directory name after the last dot.
        role_name = ""
        role_path = find_role_dir(file.path)
        if role_path is not None:
            meta = role_path / "meta" / "main.yml"
            if meta.is_file():
                meta_data = parse_yaml_from_file(str(meta))
                if isinstance(meta_data, dict):
                    galaxy_info = meta_data.get("galaxy_info")
                    if isinstance(galaxy_info, dict):
                        value = galaxy_info.get("role_name")
                        if isinstance(value, str) and value.isidentifier():
                            role_name = value
        if not role_name:
            candidate = file.role.rsplit(".", 1)[-1]
            if candidate.isidentifier():
                role_name = candidate
        if not role_name:
            return Prefix(unknown=file.role)
        return Prefix(role_name)

    def _parse_prefix(self, fqcn: str) -> Prefix:
        name = fqcn.split("/")[-1]
        unknown = ""
        if name.count(".") == 1:
            # A 'namespace.role' name from a Galaxy install: the prefix is the
            # role part of the name. Longer dotted names are collection FQCNs,
            # whose foreign variables stay exempted from this check.
            name = name.rsplit(".", 1)[-1]
            if not name.isidentifier():
                name, unknown = "", fqcn
        elif "." in name:
            name = ""
        return Prefix(name, is_fqcn(fqcn), unknown)


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
        app: App,
    ) -> None:
        """Test rule matches."""
        rules = RulesCollection(app=app, options=config_options)
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
            ("var-naming[no-keyword]", 10),
            ("var-naming[non-ascii]", 11),
            ("var-naming[no-reserved]", 12),
            ("var-naming[read-only]", 13),
        )
        assert len(results) == len(expected_errors)
        for idx, result in enumerate(results):
            assert result.tag == expected_errors[idx][0]
            assert result.lineno == expected_errors[idx][1]

    def test_invalid_vars_diff_files(
        default_rules_collection: RulesCollection,
    ) -> None:
        """Test rule matches."""
        results = Runner(
            Lintable("examples/playbooks/vars/rule_var_naming_fails_files"),
            rules=default_rules_collection,
        ).run()
        expected_errors = (
            ("var-naming[pattern]", 2),
            ("var-naming[pattern]", 3),
            ("var-naming[pattern]", 2),
            ("var-naming[pattern]", 3),
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
        assert len(results) == 4
        for result in results:
            assert result.tag == "var-naming[no-role-prefix]"

    @pytest.mark.libyaml
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

    def test_var_naming_connection_vars_in_role() -> None:
        """Connection variables must not require a role prefix."""
        rule = VariableNamingRule()
        file = Lintable("examples/roles/var_naming_no_role_prefix/tasks/main.yml")
        prefix = Prefix("var_naming_no_role_prefix")
        for ident in (
            "ansible_ssh_common_args",
            "ansible_ssh_extra_args",
            "ansible_port",
        ):
            assert (
                rule.get_var_naming_matcherror(ident, prefix=prefix, file=file) is None
            )

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

    def test_var_naming_with_pattern_foreign_role() -> None:
        """Test rule matches."""
        role_path = "examples/playbooks/bug-4095.yml"
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

    def test_var_naming_with_register_projection(
        config_options: Options,
        app: App,
    ) -> None:
        """Test register projection variable names."""
        rules = RulesCollection(app=app, options=config_options)
        rules.register(VariableNamingRule())
        results = Runner(
            Lintable("test/schemas/test/playbooks/register_projection.yml"),
            rules=rules,
        ).run()
        assert not results

    def test_var_naming_with_include_role_import_role() -> None:
        """Test with include role and import role."""
        role_path = "examples/.test_collection/roles/my_role/tasks/main.yml"
        result = run_ansible_lint(role_path)
        assert result.returncode == RC.SUCCESS
        assert "var-naming" not in result.stdout

    def test_var_naming_register_set_fact_in_roles(
        default_rules_collection: RulesCollection,
    ) -> None:
        """Test register and set_fact variable naming in roles."""
        results = Runner(
            Lintable("examples/roles/var_naming_no_role_prefix/tasks/main.yml"),
            rules=default_rules_collection,
        ).run()
        expected_errors = [
            ("var-naming[no-role-prefix]", "register: bad_register_var"),
            ("var-naming[no-role-prefix]", "set_fact: bad_set_fact_var"),
            ("var-naming[no-role-prefix]", "vars: bad_included_var"),
            ("var-naming[no-role-prefix]", "vars: bad_imported_var"),
        ]
        # Filter only var-naming errors
        # var_naming_errors = [r for r in results if r.rule.id == "var-naming"]
        assert len(results) == len(expected_errors)
        for idx, result in enumerate(results):
            assert result.tag == expected_errors[idx][0]
            assert expected_errors[idx][1] in result.message

    def test_var_naming_dotted_role_dir(
        config_options: Options,
        app: App,
    ) -> None:
        """Check prefix detection on a Galaxy 'namespace.role' directory.

        The expected prefix comes from galaxy_info.role_name (dotted_role),
        while include_role/import_role vars use the role part of the dotted
        name (dotted_target).
        See: https://github.com/ansible/ansible-lint/issues/5215
        """
        rules = RulesCollection(app=app, options=config_options)
        rules.register(VariableNamingRule())
        results = Runner(
            Lintable("examples/roles/acme.var_naming_dotted"),
            rules=rules,
        ).run()
        expected_messages = sorted(
            f"Variables names from within roles should use {prefix} as a prefix. {suffix}"
            for prefix, suffix in (
                ("dotted_role_", "(vars: var_naming_dotted_decoy)"),
                ("dotted_role_", "(vars: bad_default_var)"),
                ("dotted_role_", "(set_fact: bad_set_fact_var)"),
                ("dotted_target_", "(vars: bad_included_var)"),
                ("dotted_target_", "(vars: bad_imported_var)"),
            )
        )
        assert sorted(result.message for result in results) == expected_messages
        for result in results:
            assert result.tag == "var-naming[no-role-prefix]"

    def test_var_naming_dotted_role_dir_fallback(
        config_options: Options,
        app: App,
    ) -> None:
        """Without meta/main.yml the prefix is the name after the last dot.

        See: https://github.com/ansible/ansible-lint/issues/5215
        """
        rules = RulesCollection(app=app, options=config_options)
        rules.register(VariableNamingRule())
        results = Runner(
            Lintable("examples/roles/acme.dotted_fallback"),
            rules=rules,
        ).run()
        expected_messages = sorted(
            f"Variables names from within roles should use dotted_fallback_ as a prefix. {suffix}"
            for suffix in (
                "(vars: bad_fallback_var)",
                "(set_fact: bad_fallback_fact)",
            )
        )
        assert sorted(result.message for result in results) == expected_messages
        for result in results:
            assert result.tag == "var-naming[no-role-prefix]"

    def test_var_naming_undetermined_role_prefix() -> None:
        """A role name that yields no usable prefix is reported, not skipped."""
        rule = VariableNamingRule()
        file = Lintable("examples/roles/var_naming_no_role_prefix/tasks/main.yml")
        data = parse_yaml_from_file(str(file.path))
        assert isinstance(data, list)
        ident = next(iter(data[2]["ansible.builtin.set_fact"]))
        match = rule.get_var_naming_matcherror(
            ident,
            prefix=Prefix(unknown="acme."),
            file=file,
        )
        assert match is not None
        assert match.tag == "var-naming[no-role-prefix]"
        assert "'acme.'" in match.message
