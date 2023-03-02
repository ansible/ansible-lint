"""Module containing cached JSON schemas."""
from __future__ import annotations

import json
import logging

import jsonschema
import yaml
from jsonschema.exceptions import ValidationError

from ansiblelint.file_utils import Lintable
from ansiblelint.loaders import yaml_load_safe
from ansiblelint.schemas.__main__ import JSON_SCHEMAS, _schema_cache

_logger = logging.getLogger(__package__)


def validate_file_schema(file: Lintable) -> list[str]:
    """Return list of JSON validation errors found."""
    if file.kind not in JSON_SCHEMAS:
        return [f"Unable to find JSON Schema '{file.kind}' for '{file.path}' file."]
    try:
        # convert yaml to json (keys are converted to strings)
        yaml_data = yaml_load_safe(file.content)
        json_data = json.loads(json.dumps(yaml_data))
        # file.data = json_data
        jsonschema.validate(
            instance=json_data,
            schema=_schema_cache[file.kind],
        )
    except yaml.constructor.ConstructorError as exc:
        return [f"Failed to load YAML file '{file.path}': {exc.problem}"]
    except ValidationError as exc:
        return [exc.message]
    return []
