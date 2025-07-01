"""Sample filter that should raise an ImportError when used."""

from collections.abc import Callable
from typing import Any

# pylint: skip-file

DOCUMENTATION = """
name: from_yaml
description:
    - This callback just adds total play duration to the play stats.
"""


def filter_with_importerror(data: Any) -> dict[str, str]:  # noqa: ARG001
    """Sample filter.

    :return: dict
    """
    import a_module_that_does_not_exist  # type: ignore[reportMissingImports] # noqa: F401

    return {}


class FilterModule:
    """Core filter plugins."""

    def filters(self) -> dict[str, Callable[..., dict[str, str]]]:
        """Return implemented filters."""
        return {
            "filter_with_importerror": filter_with_importerror,
        }
