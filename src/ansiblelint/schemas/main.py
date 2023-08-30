"""Module containing cached JSON schemas."""
from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

import jsonschema
import yaml
from jsonschema.exceptions import ValidationError

from ansiblelint.loaders import yaml_load_safe
from ansiblelint.schemas.__main__ import JSON_SCHEMAS, _schema_cache

_logger = logging.getLogger(__package__)

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


def validate_file_schema(file: Lintable) -> list[str]:
    """Return list of JSON validation errors found."""
    schema = {}
    if file.kind not in JSON_SCHEMAS:
        return [f"Unable to find JSON Schema '{file.kind}' for '{file.path}' file."]
    try:
        # convert yaml to json (keys are converted to strings)
        yaml_data = yaml_load_safe(file.content)
        json_data = json.loads(json.dumps(yaml_data))
        schema = _schema_cache[file.kind]
        jsonschema.validate(
            instance=json_data,
            schema=schema,
        )
    except yaml.constructor.ConstructorError as exc:
        return [f"Failed to load YAML file '{file.path}': {exc.problem}"]
    except ValidationError as exc:
        message = exc.message
        documentation_url = ""
        for k in ("description", "markdownDescription"):
            if k in schema:
                # Find standalone URLs and also markdown urls.
                match = re.search(
                    r"\[.*?\]\((https?://[^\s]+)\)|https?://[^\s]+",
                    schema[k],
                )
                if match:
                    documentation_url = match[0] if match[0] else match[1]
                    break
        if documentation_url:
            if not message.endswith("."):
                message += "."
            message += f" See {documentation_url}"
        return [message]
    return []
