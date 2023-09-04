"""Module containing cached JSON schemas."""
from __future__ import annotations

import json
import logging
import re
import typing
from typing import TYPE_CHECKING

import jsonschema
import yaml
from jsonschema.exceptions import ValidationError

from ansiblelint.loaders import yaml_load_safe
from ansiblelint.schemas.__main__ import JSON_SCHEMAS, _schema_cache

_logger = logging.getLogger(__package__)

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


def find_best_deep_match(
    errors: jsonschema.ValidationError,
) -> jsonschema.ValidationError:
    """Return the deepest schema validation error."""

    def iter_validation_error(
        err: jsonschema.ValidationError,
    ) -> typing.Iterator[jsonschema.ValidationError]:
        if err.context:
            for e in err.context:
                yield e
                yield from iter_validation_error(e)

    return max(iter_validation_error(errors), key=_deep_match_relevance)


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

        validator = jsonschema.validators.validator_for(schema)
        v = validator(schema)
        try:
            error = next(v.iter_errors(json_data))
        except StopIteration:
            return []
        if error.context:
            error = find_best_deep_match(error)
        message = f"{error.json_path} {error.message}"

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


def _deep_match_relevance(error: jsonschema.ValidationError) -> tuple[bool | int, ...]:
    validator = error.validator
    return (
        validator not in ("anyOf", "oneOf"),  # type: ignore[comparison-overlap]
        len(error.absolute_path),
        -len(error.path),
    )
