"""ansible_compat package."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ansible-compat")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.dev1"

__all__ = ["__version__"]
