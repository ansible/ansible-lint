"""Module containing cached JSON schemas."""
# pragma: no cover
import sys

from ansiblelint.schemas.main import refresh_schemas

if __name__ == "__main__":

    if refresh_schemas():
        # flake8: noqa: T201
        print("Schemas were updated.")
        sys.exit(1)
    else:
        # flake8: noqa: T201
        print("Schemas not updated", 0)
