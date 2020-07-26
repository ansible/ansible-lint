"""Utility functions related to file operations."""
import os
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from pathlib import Path
# idiom: https://github.com/python/typeshed/issues/3500#issuecomment-560958608
if sys.version_info >= (3, 8):
    from typing import TypedDict  # pylint: disable=no-name-in-module,ungrouped-imports
else:
    from typing_extensions import TypedDict


def normpath(path: Union[str, "Path"]) -> str:
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


TargetFile = TypedDict(
    "TargetFile",
    {
        'path': str,
        'type': str,  # TODO: check for FileType
        'absolute_directory': Optional[str]
    },
    total=False)
"""TargetFile identifies a file or path to be linted."""
