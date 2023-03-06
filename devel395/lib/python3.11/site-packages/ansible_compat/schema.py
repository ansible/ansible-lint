"""Utils for JSON Schema validation."""
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence, Union

import jsonschema
from jsonschema.validators import validator_for


def to_path(schema_path: Sequence[Union[str, int]]) -> str:
    """Flatten a path to a dot delimited string.

    :param schema_path: The schema path
    :returns: The dot delimited path
    """
    return ".".join(str(index) for index in schema_path)


def json_path(absolute_path: Sequence[Union[str, int]]) -> str:
    """Flatten a data path to a dot delimited string.

    :param absolute_path: The path
    :returns: The dot delimited string
    """
    path = "$"
    for elem in absolute_path:
        if isinstance(elem, int):
            path += "[" + str(elem) + "]"
        else:
            path += "." + elem
    return path


@dataclass
class JsonSchemaError:
    # pylint: disable=too-many-instance-attributes
    """Data structure to hold a json schema validation error."""

    message: str
    data_path: str
    json_path: str
    schema_path: str
    relative_schema: str
    expected: Union[bool, int, str]
    validator: str
    found: str

    @property
    def _hash_key(self) -> Any:
        # line attr is knowingly excluded, as dict is not hashable
        return (
            self.schema_path,
            self.data_path,
            self.json_path,
            self.message,
            self.expected,
        )

    def __hash__(self) -> int:
        """Return a hash value of the instance."""
        return hash(self._hash_key)

    def __eq__(self, other: object) -> bool:
        """Identify whether the other object represents the same rule match."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __lt__(self, other: object) -> bool:
        """Return whether the current object is less than the other."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return bool(self._hash_key < other._hash_key)

    def to_friendly(self) -> str:
        """Provide a friendly explanation of the error.

        :returns: The error message
        """
        return f"In '{self.data_path}': {self.message}."


def validate(
    schema: Union[str, Mapping[str, Any]], data: Dict[str, Any]
) -> List[JsonSchemaError]:
    """Validate some data against a JSON schema.

    :param schema: the JSON schema to use for validation
    :param data: The data to validate
    :returns: Any errors encountered
    """
    errors: List[JsonSchemaError] = []

    if isinstance(schema, str):
        schema = json.loads(schema)
    try:
        if not isinstance(schema, Mapping):
            raise jsonschema.SchemaError("Invalid schema, must be a mapping")
        validator = validator_for(schema)
        validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        error = JsonSchemaError(
            message=str(exc),
            data_path="schema sanity check",
            json_path="",
            schema_path="",
            relative_schema="",
            expected="",
            validator="",
            found="",
        )
        errors.append(error)
        return errors

    for validation_error in validator(schema).iter_errors(data):
        if isinstance(validation_error, jsonschema.ValidationError):
            error = JsonSchemaError(
                message=validation_error.message,
                data_path=to_path(validation_error.absolute_path),
                json_path=json_path(validation_error.absolute_path),
                schema_path=to_path(validation_error.schema_path),
                relative_schema=validation_error.schema,
                expected=validation_error.validator_value,
                validator=str(validation_error.validator),
                found=str(validation_error.instance),
            )
            errors.append(error)
    return sorted(errors)
