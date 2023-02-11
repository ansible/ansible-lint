"""Module containing cached JSON schemas."""
import sys

from ansiblelint.schemas.main import refresh_schemas

if __name__ == "__main__":
    if refresh_schemas():  # pragma: no cover
        # flake8: noqa: T201
        print("Schemas were updated.")
        sys.exit(1)
    else:  # pragma: no cover
        # flake8: noqa: T201
        print("Schemas not updated", 0)
