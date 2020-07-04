"""Utility functions related to file operations."""
import os


def normpath(path) -> str:
    """
    Normalize a path in order to provide a more consistent output.

    Currently it generates a relative path but in the future we may want to
    make this user configurable.
    """
    # convertion to string in order to allow receiving non string objects
    return os.path.relpath(str(path))
