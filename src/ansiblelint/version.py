"""Ansible-lint version information."""
try:
    from ._version import version as __version__
except ImportError:

    try:
        import pkg_resources

        __version__ = pkg_resources.get_distribution("ansible-lint").version
    except Exception:
        __version__ = "unknown"

__all__ = ("__version__",)
