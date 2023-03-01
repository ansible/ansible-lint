"""Rule definition for JSON Schema Validations."""
from __future__ import annotations

import logging
import sys
from typing import Any

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.schemas.__main__ import JSON_SCHEMAS
from ansiblelint.schemas.main import validate_file_schema

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
            "msg": "with_filetree was moved to with_community.general.flattened in 2.10",
            "tag": "moves",
        },
        "with_cartesian": {
            "msg": "with_cartesian was moved to with_community.general.flattened in 2.10",
            "tag": "moves",
        },
    }
}


class ValidateSchemaRule(AnsibleLintRule):
    """Perform JSON Schema Validation for known lintable kinds."""

    description = DESCRIPTION_MD

    id = "schema"
    severity = "VERY_HIGH"
    tags = ["core"]
    version_added = "v6.1.0"

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str | MatchError | list[MatchError]:
        result = []
        for key in pre_checks["task"]:
            if key in task:
                msg = pre_checks["task"][key]["msg"]
                tag = pre_checks["task"][key]["tag"]
                result.append(
                    MatchError(
                        message=msg,
                        filename=file,
                        rule=ValidateSchemaRule(),
                        details=ValidateSchemaRule.description,
                        tag=f"schema[{tag}]",
                    )
                )
        return result

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return JSON validation errors found as a list of MatchError(s)."""
        result = []
        if file.kind not in JSON_SCHEMAS:
            return []

        errors = validate_file_schema(file)
        if errors:
            if errors[0].startswith("Failed to load YAML file"):
                _logger.debug(
                    "Ignored failure to load %s for schema validation, as !vault may cause it."
                )
                return []

            result.append(
                MatchError(
                    message=errors[0],
                    filename=file,
                    rule=ValidateSchemaRule(),
                    details=ValidateSchemaRule.description,
                    tag=f"schema[{file.kind}]",
                )
            )
        return result


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:
    import pytest

    # pylint: disable=ungrouped-imports
    from ansiblelint.config import options
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    @pytest.mark.parametrize(
        ("file", "expected_kind", "expected"),
        (
            pytest.param(
                "examples/collection/galaxy.yml",
                "galaxy",
                ["'GPL' is not one of"],
                id="galaxy",
            ),
            pytest.param(
                "examples/roles/invalid_requirements_schema/meta/requirements.yml",
                "requirements",
                ["{'foo': 'bar'} is not valid under any of the given schemas"],
                id="requirements",
            ),
            pytest.param(
                "examples/roles/invalid_meta_schema/meta/main.yml",
                "meta",
                ["False is not of type 'string'"],
                id="meta",
            ),
            pytest.param(
                "examples/playbooks/vars/invalid_vars_schema.yml",
                "vars",
                ["'123' does not match any of the regexes"],
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
                ["Additional properties are not allowed ('foo' was unexpected)"],
                id="execution-environment-broken",
            ),
            ("examples/meta/runtime.yml", "meta-runtime", []),
            pytest.param(
                "examples/broken_collection_meta_runtime/meta/runtime.yml",
                "meta-runtime",
                ["Additional properties are not allowed ('foo' was unexpected)"],
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
                ["Additional properties are not allowed ('foo' was unexpected)"],
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
                ["Additional properties are not allowed ('foo' was unexpected)"],
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
                ["Additional properties are not allowed ('ansible' was unexpected)"],
                id="ansible-navigator-config-broken",
            ),
            pytest.param(
                "examples/roles/hello/meta/argument_specs.yml",
                "arg_specs",
                [],
                id="arg_specs",
            ),
            pytest.param(
                "examples/roles/broken_argument_specs/meta/argument_specs.yml",
                "arg_specs",
                ["Additional properties are not allowed ('foo' was unexpected)"],
                id="arg_specs-broken",
            ),
            pytest.param(
                "examples/changelogs/changelog.yaml",
                "changelog",
                ["Additional properties are not allowed ('foo' was unexpected)"],
                id="changelog",
            ),
            pytest.param(
                "examples/rulebooks/rulebook-fail.yml",
                "rulebook",
                [
                    "Additional properties are not allowed ('that_should_not_be_here' was unexpected)"
                ],
                id="rulebook",
            ),
            pytest.param(
                "examples/rulebooks/rulebook-pass.yml",
                "rulebook",
                [],
                id="rulebook2",
            ),
        ),
    )
    def test_schema(file: str, expected_kind: str, expected: list[str]) -> None:
        """Validate parsing of ansible output."""
        lintable = Lintable(file)
        assert lintable.kind == expected_kind

        rules = RulesCollection(options=options)
        rules.register(ValidateSchemaRule())
        results = Runner(lintable, rules=rules).run()

        assert len(results) == len(expected), results
        for idx, result in enumerate(results):
            assert result.filename.endswith(file)
            assert expected[idx] in result.message
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
        file: str, expected_kind: str, expected_tag: str, count: int
    ) -> None:
        """Validate ability to detect schema[moves]."""
        lintable = Lintable(file)
        assert lintable.kind == expected_kind

        rules = RulesCollection(options=options)
        rules.register(ValidateSchemaRule())
        results = Runner(lintable, rules=rules).run()

        assert len(results) == count, results
        for result in results:
            assert result.filename.endswith(file)
            assert result.tag == expected_tag
