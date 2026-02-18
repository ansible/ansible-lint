"""Implementation of role-argument-spec rule."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.app import App
    from ansiblelint.config import Options
    from ansiblelint.errors import MatchError


class RoleArgumentSpec(AnsibleLintRule):
    """Role should have an argument specification file."""

    id = "role-argument-spec"
    description = (
        "Roles should define an argument specification in "
        "``meta/argument_specs.yml`` to document and validate "
        "expected variables. This improves usability, enables "
        "validation at runtime, and generates documentation."
    )
    link = "https://docs.ansible.com/projects/ansible/devel/user_guide/playbooks_reuse_roles.html#role-argument-validation"
    severity = "HIGH"
    tags = ["metadata", "opt-in"]
    version_changed = "25.1.0"

    def matchdir(self, lintable: Lintable) -> list[MatchError]:
        """Check if a role directory contains an argument_specs file."""
        if lintable.kind != "role":
            return []

        arg_spec_yml = lintable.path / "meta" / "argument_specs.yml"
        arg_spec_yaml = lintable.path / "meta" / "argument_specs.yaml"

        meta_main_yml = lintable.path / "meta" / "main.yml"
        meta_main_yaml = lintable.path / "meta" / "main.yaml"

        has_standalone = arg_spec_yml.is_file() or arg_spec_yaml.is_file()

        if not has_standalone:
            has_embedded = False
            meta_file = None
            for meta_path in (meta_main_yml, meta_main_yaml):
                if meta_path.is_file():
                    meta_file = meta_path
                    meta_data = parse_yaml_from_file(str(meta_path))
                    if (
                        meta_data
                        and isinstance(meta_data, dict)
                        and "argument_specs" in meta_data
                    ):
                        has_embedded = True
                        break

            if not has_embedded:
                # Report against meta/main.yml when it exists so
                # inline skip comments and ignore file entries work.
                # Fall back to the role directory if no meta file exists.
                target = Lintable(meta_file) if meta_file else lintable
                return [
                    self.create_matcherror(
                        message="Role is missing an argument specification file (meta/argument_specs.yml).",
                        filename=target,
                    ),
                ]

        return []


if "pytest" in sys.modules:
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_role_argument_spec_missing(
        config_options: Options,
        app: App,
    ) -> None:
        """Role without argument_specs should trigger the rule."""
        config_options.enable_list = ["role-argument-spec"]
        rules = RulesCollection(app=app, options=config_options)
        rules.register(RoleArgumentSpec())
        results = Runner(
            "examples/roles/role_argument_spec_missing",
            rules=rules,
        ).run()
        matched = [r for r in results if r.rule.id == "role-argument-spec"]
        assert len(matched) == 1

    def test_role_argument_spec_present_standalone(
        config_options: Options,
        app: App,
    ) -> None:
        """Role with a standalone argument_specs.yml should pass."""
        config_options.enable_list = ["role-argument-spec"]
        rules = RulesCollection(app=app, options=config_options)
        rules.register(RoleArgumentSpec())
        results = Runner(
            "examples/roles/hello",
            rules=rules,
        ).run()
        matched = [r for r in results if r.rule.id == "role-argument-spec"]
        assert len(matched) == 0

    def test_role_argument_spec_present_embedded(
        config_options: Options,
        app: App,
    ) -> None:
        """Role with argument_specs in meta/main.yml should pass."""
        config_options.enable_list = ["role-argument-spec"]
        rules = RulesCollection(app=app, options=config_options)
        rules.register(RoleArgumentSpec())
        results = Runner(
            "examples/roles/role_argument_spec_embedded",
            rules=rules,
        ).run()
        matched = [r for r in results if r.rule.id == "role-argument-spec"]
        assert len(matched) == 0
