"""Sample adjacent filter plugin."""

from __future__ import annotations


class FilterModule:  # pylint: disable=too-few-public-methods
    """Ansible filters."""

    def filters(self):  # type: ignore[no-untyped-def]
        """Return list of exposed filters."""
        return {
            "some_filter": str,
        }
