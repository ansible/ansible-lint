"""Utility functions related to file operations."""
import os
from contextlib import contextmanager


def normpath(path) -> str:
    """
    Normalize a path in order to provide a more consistent output.

    Currently it generates a relative path but in the future we may want to
    make this user configurable.
    """
    # convertion to string in order to allow receiving non string objects
    return os.path.relpath(str(path))


@contextmanager
def cwd(path):
    """Context manager for temporary changing current working directory."""
    old_pwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_pwd)
