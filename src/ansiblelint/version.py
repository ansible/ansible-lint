"""Ansible-lint version information."""
try:
    from ._version import version as __version__
except ImportError:

    try:
        import pkg_resources

        __version__ = pkg_resources.get_distribution("ansible-lint").version
    except Exception:  # pylint: disable=broad-except
        __version__ = "unknown"

__all__ = ("__version__",)
