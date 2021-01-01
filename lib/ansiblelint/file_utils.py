"""Utility functions related to file operations."""
import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, List, Optional, Union

from ansiblelint.constants import FileType

if TYPE_CHECKING:
    # https://github.com/PyCQA/pylint/issues/3979
    BasePathLike = os.PathLike[Any]  # pylint: disable=unsubscriptable-object
else:
    BasePathLike = os.PathLike


def normpath(path: Union[str, BasePathLike]) -> str:
    """
    Normalize a path in order to provide a more consistent output.

    Currently it generates a relative path but in the future we may want to
    make this user configurable.
    """
    # convertion to string in order to allow receiving non string objects
    return os.path.relpath(str(path))


@contextmanager
def cwd(path: Union[str, BasePathLike]) -> Iterator[None]:
    """Context manager for temporary changing current working directory."""
    old_pwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_pwd)


def expand_path_vars(path: str) -> str:
    """Expand the environment or ~ variables in a path string."""
    # It may be possible for function to be called with a Path object
    path = str(path).strip()
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return path


def expand_paths_vars(paths: List[str]) -> List[str]:
    """Expand the environment or ~ variables in a list."""
    paths = [expand_path_vars(p) for p in paths]
    return paths


class Lintable:
    """Defines a file/folder that can be linted.

    Providing file content when creating the object allow creation of in-memory
    instances that do not need files to be present on disk.
    """

    def __init__(self, name: str, content: Optional[str] = None, kind: Optional[FileType] = None):
        """Create a Lintable instance."""
        self.name = name
        self.path = Path(name)
        self._content = content
        # TODO(ssbarnea): implement kind detection when not provided
        self.kind = kind

    @property
    def content(self) -> str:
        """Retried file content, from internal cache or disk."""
        if self._content is None:
            with open(self.name, mode='r', encoding='utf-8') as f:
                self._content = f.read()
        return self._content
