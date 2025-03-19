"""Ansible-lint version information."""

# this is the fallback SemVer version picked by setuptools_scm when tag
# information is not available.
__version__ = "0.1.dev1"
__all__ = ("__version__",)
from typing import TYPE_CHECKING

# as either pyright or mypy have problems with these import fallbacks, we
# avoid running them when doing type checking
if not TYPE_CHECKING:
    try:
        from ._version import version as __version__
    except ImportError:  # pragma: no cover
        try:
            import pkg_resources  # pylint: disable=import-error

            __version__ = pkg_resources.get_distribution("ansible-lint").version
        except Exception:  # pylint: disable=broad-except  # noqa: BLE001, S110
            pass
