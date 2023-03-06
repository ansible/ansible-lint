"""Portability helpers."""
import sys
from functools import cached_property

if sys.version_info >= (3, 9):
    from functools import cache  # pylint: disable=no-name-in-module
else:  # pragma: no cover
    from functools import lru_cache

    cache = lru_cache(maxsize=None)


__all__ = ["cache", "cached_property"]
