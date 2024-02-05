"""Ansible-lint version information."""

try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    try:
        import pkg_resources

        __version__ = pkg_resources.get_distribution("ansible-lint").version
    except Exception:  # pylint: disable=broad-except # noqa: BLE001
        # this is the fallback SemVer version picked by setuptools_scm when tag
        # information is not available.
        __version__ = "0.1.dev1"

__all__ = ("__version__",)
