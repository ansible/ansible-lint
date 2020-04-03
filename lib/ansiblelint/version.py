"""Ansible-lint version information."""

try:
    import pkg_resources
except ImportError:
    pass


try:
    __version__ = pkg_resources.get_distribution('ansible-lint').version
except Exception:
    __version__ = 'unknown'
