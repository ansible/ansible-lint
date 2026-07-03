"""Module containing cached JSON schemas."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ansiblelint.loaders import yaml_load_safe
from ansiblelint.schemas.__main__ import JSON_SCHEMAS, _schema_cache

_logger = logging.getLogger(__package__)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ansiblelint.file_utils import Lintable


RE_MD_URLS = re.compile(
    r"\[.{0,256}?\]\((?P<url>https?://[^\s]+)\)|(?P<url2>https?://[^\s]+)"
)


def find_best_deep_match(
    errors: ValidationError,
) -> ValidationError:
    """Return the deepest schema validation error."""

    def iter_validation_error(
        err: ValidationError,
    ) -> Iterator[ValidationError]:
        if err.context:
            for e in err.context:
                yield e
                yield from iter_validation_error(e)

    return max(iter_validation_error(errors), key=_deep_match_relevance)


def _find_documentation_url(*schemas: dict[Any, Any]) -> str:
    """Search schemas for a documentation URL."""
    for json_schema in schemas:
        for k in ("description", "markdownDescription"):
            if k in json_schema:
                match = RE_MD_URLS.search(json_schema[k])
                if match:
                    return next(x for x in match.groups() if x is not None)
    return ""


def _format_validation_message(
    error: ValidationError,
    schema: dict[Any, Any],
) -> str:
    """Format a validation error into a user-facing message."""
    if not hasattr(error, "schema") or not isinstance(
        error.schema, dict
    ):  # pragma: no cover
        msg = "error object does not have schema attribute"
        raise TypeError(msg)
    if "not" in error.schema and len(error.schema["not"]) == 0:
        message: str = error.schema["title"]
        schema = error.schema
    else:
        message = f"{error.json_path} {error.message}"

    documentation_url = _find_documentation_url(error.schema, schema)
    if documentation_url:
        if not message.endswith("."):
            message += "."
        message += f" See {documentation_url}"
    return message


def _validate_json_data(
    json_data: Any,
    schema: dict[Any, Any],
) -> str | None:
    """Validate JSON data against schema, return message or None if valid."""
    validator = Draft202012Validator(schema)
    try:
        error = next(validator.iter_errors(json_data))
    except StopIteration:
        return None
    if error.context:
        error = find_best_deep_match(error)
    return _format_validation_message(error, schema)


def validate_file_schema(file: Lintable) -> list[str]:
    """Return list of JSON validation errors found."""
    schema: dict[Any, Any] = {}
    if file.kind not in JSON_SCHEMAS:
        return [f"Unable to find JSON Schema '{file.kind}' for '{file.path}' file."]
    try:
        yaml_data = yaml_load_safe(file.content)
        json_data = json.loads(json.dumps(yaml_data))
        schema = _schema_cache[file.kind]
        message = _validate_json_data(json_data, schema)
        if message is None:
            return []
    except yaml.constructor.ConstructorError as exc:
        return [f"Failed to load YAML file '{file.path}': {exc.problem}"]
    except ValidationError as exc:  # pragma: no cover
        message = exc.message
        documentation_url = _find_documentation_url(schema)
        if documentation_url:
            if not message.endswith("."):
                message += "."
            message += f" See {documentation_url}"
        return [message]
    return [message]


def _deep_match_relevance(error: ValidationError) -> tuple[bool | int, ...]:
    validator = error.validator
    return (
        validator not in ("anyOf", "oneOf"),
        len(error.absolute_path),
        -len(error.path),
    )
