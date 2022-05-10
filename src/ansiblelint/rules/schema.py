"""Rule definition for JSON Schema Validations."""
import json
import logging
import os
import sys
from functools import lru_cache
from typing import Any, List

import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ansiblelint.config import JSON_SCHEMAS
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.schemas import __file__ as schemas_module

_logger = logging.getLogger(__name__)


class ValidateSchemaRule(AnsibleLintRule):
    """Perform JSON Schema Validation for known lintable kinds.

    Returned errors will not include exact line numbers, but they will mention
    the schema name being used as a tag, like ``playbook-schema``,
    ``tasks-schema``.

    This rule is not skippable and stops further processing of the file.

    Schema bugs should be reported towards https://github.com/ansible/schemas
    project instead of ansible-lint.

    If incorrect schema was picked, you might want to either:

    * move the file to standard location, so its file is detected correctly.
    * use ``kinds:`` option in linter config to help it pick correct file type.
    """

    id = "schema"
    description = __doc__
    severity = "VERY_HIGH"
    tags = ["core", "experimental"]
    version_added = "v6.1.0"

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_schema(kind: str) -> Any:
        """Return the schema for the given kind."""
        schema_file = os.path.dirname(schemas_module) + "/" + kind + ".json"
        with open(schema_file, encoding="utf-8") as f:
            return json.load(f)

    def matchyaml(self, file: Lintable) -> List[MatchError]:
        """Return JSON validation errors found as a list of MatchError(s)."""
        result = []
        if file.kind not in JSON_SCHEMAS:
            return []

        try:
            # convert yaml to json (keys are converted to strings)
            yaml_data = yaml.safe_load(file.content)
            json_data = json.loads(json.dumps(yaml_data))
            validate(
                instance=json_data,
                schema=ValidateSchemaRule._get_schema(file.kind),
            )
        except yaml.constructor.ConstructorError:
            _logger.debug(
                "Ignored failure to load %s for schema validation, as !vault may cause it."
            )
            return []
        except ValidationError as exc:
            result.append(
                MatchError(
                    message=exc.message,
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
            (
                "examples/galaxy.yml",
                "galaxy",
                ["'GPL' is not one of"],
            ),
            (
                "examples/roles/invalid_requirements_schema/meta/requirements.yml",
                "requirements",
                ["'collections' is a required property"],
            ),
            (
                "examples/roles/invalid_meta_schema/meta/main.yml",
                "meta",
                ["False is not of type 'string'"],
            ),
            (
                "examples/playbooks/vars/invalid_vars_schema.yml",
                "vars",
                ["'123' does not match any of the regexes"],
            ),
        ),
        ids=(
            # "playbook-fail",
            "galaxy",
            "requirements",
            "meta",
            "vars",
        ),
    )
    # # unsupported yet:
    # "execution-environment": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-ee.json",
    # "meta-runtime": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-meta-runtime.json",
    # "inventory": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-inventory.json",
    # "ansible-lint-config": "https://raw.githubusercontent.com/ansible/schemas/main/f/ansible-lint.json",
    # "ansible-navigator-config": "https://raw.githubusercontent.com/ansible/ansible-navigator/main/src/ansible_navigator/data/ansible-navigator.json",
    def test_schema(file: str, expected_kind: str, expected: List[str]) -> None:
        """Validate parsing of ansible output."""
        lintable = Lintable(file)
        assert lintable.kind == expected_kind

        rules = RulesCollection(options=options)
        rules.register(ValidateSchemaRule())
        results = Runner(lintable, rules=rules).run()

        # ValidateSchemaRule.process_lintable(lintable)
        assert len(results) == len(expected), results
        for idx, result in enumerate(results):
            assert result.filename.endswith(file)
            assert expected[idx] in result.message
            assert result.tag == f"schema[{expected_kind}]"
