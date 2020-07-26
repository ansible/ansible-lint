"""Utility functions related to file operations."""
import os
import sys
from typing import TYPE_CHECKING, Optional, Union

from ansiblelint.constants import FileType

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


class TargetFile(TypedDict):
    """TargetFile identifies a file or path to be linted."""

    path: str
    type: Optional[FileType]
