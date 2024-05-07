"""Rule definition for JSON Schema Validations."""

from __future__ import annotations

import logging
import re
import sys
from typing import TYPE_CHECKING, Any

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.schemas.__main__ import JSON_SCHEMAS
from ansiblelint.schemas.main import validate_file_schema
from ansiblelint.text import has_jinja

if TYPE_CHECKING:
    from ansiblelint.config import Options
    from ansiblelint.utils import Task


_logger = logging.getLogger(__name__)


DESCRIPTION_MD = """ Returned errors will not include exact line numbers, but they will mention
the schema name being used as a tag, like ``schema[playbook]``,
``schema[tasks]``.

This rule is not skippable and stops further processing of the file.

If incorrect schema was picked, you might want to either:

* move the file to standard location, so its file is detected correctly.
* use ``kinds:`` option in linter config to help it pick correct file type.
"""

pre_checks = {
    "task": {
        "with_flattened": {
            "msg": "with_flattened was moved to with_community.general.flattened in 2.10",
            "tag": "moves",
        },
        "with_filetree": {
            "msg": "with_filetree was moved to with_community.general.filetree in 2.10",
            "tag": "moves",
        },
        "with_cartesian": {
            "msg": "with_cartesian was moved to with_community.general.flattened in 2.10",
            "tag": "moves",
        },
    },
}


class ValidateSchemaRule(AnsibleLintRule):
    """Perform JSON Schema Validation for known lintable kinds."""

    description = DESCRIPTION_MD

    id = "schema"
    severity = "VERY_HIGH"
    tags = ["core"]
    version_added = "v6.1.0"
    _ids = {
        "schema[ansible-lint-config]": "",
        "schema[ansible-navigator-config]": "",
        "schema[changelog]": "",
        "schema[execution-environment]": "",
        "schema[galaxy]": "",
        "schema[inventory]": "",
        "schema[meta]": "",
        "schema[meta-runtime]": "",
        "schema[molecule]": "",
        "schema[playbook]": "",
        "schema[requirements]": "",
        "schema[role-arg-spec]": "",
        "schema[rulebook]": "",
        "schema[tasks]": "",
        "schema[vars]": "",
    }
    _field_checks: dict[str, list[str]] = {}

    @property
    def field_checks(self) -> dict[str, list[str]]:
        """Lazy property for returning field checks."""
        if not self._collection:
            msg = "Rule was not registered to a RuleCollection."
            raise RuntimeError(msg)
        if not self._field_checks:
            self._field_checks = {
                "become_method": sorted(
                    self._collection.app.runtime.plugins.become.keys(),
                ),
            }
        return self._field_checks

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific playbook."""
        results: list[MatchError] = []
        if (
            not data
            or file.kind not in ("tasks", "handlers", "playbook")
            or file.failed()
        ):
            return results
        # check at play level
        results.extend(self._get_field_matches(file=file, data=data))
        return results

    def _get_field_matches(
        self,
        file: Lintable,
        data: dict[str, Any],
    ) -> list[MatchError]:
        """Retrieve all matches related to fields for the given data block."""
        results = []
        for key, values in self.field_checks.items():
            if key in data:
                plugin_value = data[key]
                if not has_jinja(plugin_value) and plugin_value not in values:
                    msg = f"'{key}' must be one of the currently available values: {', '.join(values)}"
                    results.append(
                        MatchError(
                            message=msg,
                            lineno=data.get("__line__", 1),
                            lintable=file,
                            rule=self,
                            details=ValidateSchemaRule.description,
                            tag=f"schema[{file.kind}]",
                        ),
                    )
        return results

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str | MatchError | list[MatchError]:
        results: list[MatchError] = []
        if not file:
            file = Lintable("", kind="tasks")

        if file.failed():
            return results

        results.extend(self._get_field_matches(file=file, data=task.raw_task))
        for key in pre_checks["task"]:
            if key in task.raw_task:
                msg = pre_checks["task"][key]["msg"]
                tag = pre_checks["task"][key]["tag"]
                results.append(
                    MatchError(
                        message=msg,
                        lintable=file,
                        rule=self,
                        details=ValidateSchemaRule.description,
                        tag=f"schema[{tag}]",
                    ),
                )
        return results

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return JSON validation errors found as a list of MatchError(s)."""
        result: list[MatchError] = []

        if file.failed():
            return result

        if file.kind not in JSON_SCHEMAS:
            return result

        for error in validate_file_schema(file):
            if error.startswith("Failed to load YAML file"):
                _logger.debug(
                    "Ignored failure to load %s for schema validation, as !vault may cause it.",
                    file,
                )
                return []

            result.append(
                MatchError(
                    message=error,
                    lintable=file,
                    rule=self,
                    details=ValidateSchemaRule.description,
                    tag=f"schema[{file.kind}]",
                ),
            )
            break

        if not result:
            result = super().matchyaml(file)
        return result


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected_kind", "expected"),
        (
            pytest.param(
                "examples/.collection/galaxy.yml",
                "galaxy",
                [r".*'GPL' is not one of.*https://"],
                id="galaxy",
            ),
            pytest.param(
                "examples/roles/invalid_requirements_schema/meta/requirements.yml",
                "requirements",
                [
                    # r".*{'foo': 'bar'} is not valid under any of the given schemas.*https://",
                    r".*{'foo': 'bar'} is not of type 'array'.*https://",
                ],
                id="requirements",
            ),
            pytest.param(
                "examples/roles/invalid_meta_schema/meta/main.yml",
                "meta",
                [r".*False is not of type 'string'.*https://"],
                id="meta",
            ),
            pytest.param(
                "examples/playbooks/vars/invalid_vars_schema.yml",
                "vars",
                [r".* '123' does not match any of the regexes.*https://"],
                id="vars",
            ),
            pytest.param(
                "examples/execution-environment.yml",
                "execution-environment",
                [],
                id="execution-environment",
            ),
            pytest.param(
                "examples/ee_broken/execution-environment.yml",
                "execution-environment",
                [
                    r".*Additional properties are not allowed \('foo' was unexpected\).*https://",
                ],
                id="execution-environment-broken",
            ),
            pytest.param(
                "examples/meta/runtime.yml",
                "meta-runtime",
                [],
                id="meta-runtime",
            ),
            pytest.param(
                "examples/broken_collection_meta_runtime/meta/runtime.yml",
                "meta-runtime",
                [
                    r".*Additional properties are not allowed \('foo' was unexpected\).*https://",
                ],
                id="meta-runtime-broken",
            ),
            pytest.param(
                "examples/inventory/production.yml",
                "inventory",
                [],
                id="inventory",
            ),
            pytest.param(
                "examples/inventory/broken_dev_inventory.yml",
                "inventory",
                [
                    r".*Additional properties are not allowed \('foo' was unexpected\).*https://",
                ],
                id="inventory-broken",
            ),
            pytest.param(
                ".ansible-lint",
                "ansible-lint-config",
                [],
                id="ansible-lint-config",
            ),
            pytest.param(
                "examples/.config/ansible-lint.yml",
                "ansible-lint-config",
                [],
                id="ansible-lint-config2",
            ),
            pytest.param(
                "examples/broken/.ansible-lint",
                "ansible-lint-config",
                [
                    r".*Additional properties are not allowed \('foo' was unexpected\).*https://",
                ],
                id="ansible-lint-config-broken",
            ),
            pytest.param(
                "examples/ansible-navigator.yml",
                "ansible-navigator-config",
                [],
                id="ansible-navigator-config",
            ),
            pytest.param(
                "examples/broken/ansible-navigator.yml",
                "ansible-navigator-config",
                [
                    r".*Additional properties are not allowed \('ansible' was unexpected\).*https://",
                ],
                id="ansible-navigator-config-broken",
            ),
            pytest.param(
                "examples/roles/hello/meta/argument_specs.yml",
                "role-arg-spec",
                [],
                id="role-arg-spec",
            ),
            pytest.param(
                "examples/roles/broken_argument_specs/meta/argument_specs.yml",
                "role-arg-spec",
                [
                    r".*Additional properties are not allowed \('foo' was unexpected\).*https://",
                ],
                id="role-arg-spec-broken",
            ),
            pytest.param(
                "examples/changelogs/changelog.yaml",
                "changelog",
                [
                    r".*Additional properties are not allowed \('foo' was unexpected\).*https://",
                ],
                id="changelog",
            ),
            pytest.param(
                "examples/rulebooks/rulebook-fail.yml",
                "rulebook",
                [
                    # r".*Additional properties are not allowed \('that_should_not_be_here' was unexpected\).*https://",
                    r".*'sss' is not of type 'object'.*https://",
                ],
                id="rulebook",
            ),
            pytest.param(
                "examples/rulebooks/rulebook-pass.yml",
                "rulebook",
                [],
                id="rulebook2",
            ),
            pytest.param(
                "examples/playbooks/rule-schema-become-method-pass.yml",
                "playbook",
                [],
                id="playbook",
            ),
            pytest.param(
                "examples/playbooks/rule-schema-become-method-fail.yml",
                "playbook",
                [
                    "'become_method' must be one of the currently available values",
                    "'become_method' must be one of the currently available values",
                ],
                id="playbook2",
            ),
        ),
    )
    def test_schema(
        file: str,
        expected_kind: str,
        expected: list[str],
        config_options: Options,
    ) -> None:
        """Validate parsing of ansible output."""
        lintable = Lintable(file)
        assert lintable.kind == expected_kind

        rules = RulesCollection(options=config_options)
        rules.register(ValidateSchemaRule())
        results = Runner(lintable, rules=rules).run()

        assert len(results) == len(expected), results
        for idx, result in enumerate(results):
            assert result.filename.endswith(file)
            assert re.match(expected[idx], result.message)
            assert result.tag == f"schema[{expected_kind}]"

    @pytest.mark.parametrize(
        ("file", "expected_kind", "expected_tag", "count"),
        (
            pytest.param(
                "examples/playbooks/rule-syntax-moves.yml",
                "playbook",
                "schema[moves]",
                3,
                id="playbook",
            ),
        ),
    )
    def test_schema_moves(
        file: str,
        expected_kind: str,
        expected_tag: str,
        count: int,
        config_options: Options,
    ) -> None:
        """Validate ability to detect schema[moves]."""
        lintable = Lintable(file)
        assert lintable.kind == expected_kind

        rules = RulesCollection(options=config_options)
        rules.register(ValidateSchemaRule())
        results = Runner(lintable, rules=rules).run()

        assert len(results) == count, results
        for result in results:
            assert result.filename.endswith(file)
            assert result.tag == expected_tag
