"""Module containing cached JSON schemas."""
# pragma: no cover
import sys

from ansiblelint.schemas.main import refresh_schemas

if __name__ == "__main__":

    if refresh_schemas():
        print("Schemas were updated.")
        sys.exit(1)
    else:
        print("Schemas not updated", 0)
