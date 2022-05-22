"""Utility functions related to file operations."""
import copy
import logging
import os
import pathlib
import subprocess
import sys
from argparse import Namespace
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Set, Union, cast

# import wcmatch
import wcmatch.pathlib
from wcmatch.wcmatch import RECURSIVE, WcMatch

from ansiblelint.config import BASE_KINDS, options
from ansiblelint.constants import FileType

if TYPE_CHECKING:
    # https://github.com/PyCQA/pylint/issues/3979
    BasePathLike = os.PathLike[Any]  # pylint: disable=unsubscriptable-object
else:
    BasePathLike = os.PathLike

_logger = logging.getLogger(__package__)


def abspath(path: str, base_dir: str) -> str:
    """Make relative path absolute relative to given directory.

    Args:
       path (str): the path to make absolute
       base_dir (str): the directory from which make \
                       relative paths absolute
    """
    if not os.path.isabs(path):
        # Don't use abspath as it assumes path is relative to cwd.
        # We want it relative to base_dir.
        path = os.path.join(base_dir, path)

    return os.path.normpath(path)


def normpath(path: Union[str, BasePathLike]) -> str:
    """
    Normalize a path in order to provide a more consistent output.

    Currently it generates a relative path but in the future we may want to
    make this user configurable.
    """
    # prevent possible ValueError with relpath(), when input is an empty string
    if not path:
        path = "."
    # conversion to string in order to allow receiving non string objects
    relpath = os.path.relpath(str(path))
    path_absolute = os.path.abspath(str(path))
    # we avoid returning relative paths that end-up at root level
    if path_absolute in relpath:
        return path_absolute
    return relpath


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


def kind_from_path(path: Path, base: bool = False) -> FileType:
    """Determine the file kind based on its name.

    When called with base=True, it will return the base file type instead
    of the explicit one. That is expected to return 'yaml' for any yaml files.
    """
    # pathlib.Path.match patterns are very limited, they do not support *a*.yml
    # glob.glob supports **/foo.yml but not multiple extensions
    pathex = wcmatch.pathlib.PurePath(str(path.absolute().resolve()))
    kinds = options.kinds if not base else BASE_KINDS
    for entry in kinds:
        for k, v in entry.items():
            if pathex.globmatch(
                v,
                flags=(
                    wcmatch.pathlib.GLOBSTAR
                    | wcmatch.pathlib.BRACE
                    | wcmatch.pathlib.DOTGLOB
                ),
            ):
                return str(k)  # type: ignore

    if base:
        # Unknown base file type is default
        return ""

    if path.is_dir():
        return "role"

    if str(path) == "/dev/stdin":
        return "playbook"

    # Unknown file types report a empty string (evaluated as False)
    return ""


# pylint: disable=too-many-instance-attributes
class Lintable:
    """Defines a file/folder that can be linted.

    Providing file content when creating the object allow creation of in-memory
    instances that do not need files to be present on disk.
    """

    def __init__(
        self,
        name: Union[str, Path],
        content: Optional[str] = None,
        kind: Optional[FileType] = None,
    ):
        """Create a Lintable instance."""
        # Filename is effective file on disk, for stdin is a namedtempfile
        self.filename: str = str(name)
        self.dir: str = ""
        self.kind: Optional[FileType] = None

        if isinstance(name, str):
            self.name = normpath(name)
            self.path = Path(self.name)
        else:
            self.name = str(name)
            self.path = name
        self._content = self._original_content = content
        self.updated = False

        # if the lintable is part of a role, we save role folder name
        self.role = ""
        parts = self.path.parent.parts
        if "roles" in parts:
            role = self.path
            while role.parent.name != "roles" and role.name:
                role = role.parent
            if role.exists:
                self.role = role.name

        if str(self.path) in ["/dev/stdin", "-"]:
            # pylint: disable=consider-using-with
            self.file = NamedTemporaryFile(mode="w+", suffix="playbook.yml")
            self.filename = self.file.name
            self._content = sys.stdin.read()
            self.file.write(self._content)
            self.file.flush()
            self.path = Path(self.file.name)
            self.name = "stdin"
            self.kind = "playbook"
            self.dir = "/"
        else:
            self.kind = kind or kind_from_path(self.path)
        # We store absolute directory in dir
        if not self.dir:
            if self.kind == "role":
                self.dir = str(self.path.resolve())
            else:
                self.dir = str(self.path.parent.resolve())

        # determine base file kind (yaml, xml, ini, ...)
        self.base_kind = kind_from_path(self.path, base=True)

    def __getitem__(self, key: Any) -> Any:
        """Provide compatibility subscriptable support."""
        if key == "path":
            return str(self.path)
        if key == "type":
            return str(self.kind)
        raise NotImplementedError()

    def get(self, key: Any, default: Any = None) -> Any:
        """Provide compatibility subscriptable support."""
        try:
            return self[key]
        except NotImplementedError:
            return default

    def _populate_content_cache_from_disk(self) -> None:
        # Can raise UnicodeDecodeError
        self._content = self.path.resolve().read_text(encoding="utf-8")
        if self._original_content is None:
            self._original_content = self._content

    @property
    def content(self) -> str:
        """Retrieve file content, from internal cache or disk."""
        if self._content is None:
            self._populate_content_cache_from_disk()
        return cast(str, self._content)

    @content.setter
    def content(self, value: str) -> None:
        """Update ``content`` and calculate ``updated``.

        To calculate ``updated`` this will read the file from disk if the cache
        has not already been populated.
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected str but got {type(value)}")
        if self._original_content is None:
            if self._content is not None:
                self._original_content = self._content
            elif self.path.exists():
                self._populate_content_cache_from_disk()
            else:
                # new file
                self._original_content = ""
        self.updated = self._original_content != value
        self._content = value

    @content.deleter
    def content(self) -> None:
        """Reset the internal content cache."""
        self._content = None

    def write(self, force: bool = False) -> None:
        """Write the value of ``Lintable.content`` to disk.

        This only writes to disk if the content has been updated (``Lintable.updated``).
        For example, you can update the content, and then write it to disk like this:

        .. code:: python

            lintable.content = new_content
            lintable.write()

        Use ``force=True`` when you want to force a content rewrite even if the
        content has not changed. For example:

        .. code:: python

            lintable.write(force=True)
        """
        if not force and not self.updated:
            # No changes to write.
            return
        self.path.resolve().write_text(self._content or "", encoding="utf-8")

    def __hash__(self) -> int:
        """Return a hash value of the lintables."""
        return hash((self.name, self.kind))

    def __eq__(self, other: object) -> bool:
        """Identify whether the other object represents the same rule match."""
        if isinstance(other, Lintable):
            return bool(self.name == other.name and self.kind == other.kind)
        return False

    def __repr__(self) -> str:
        """Return user friendly representation of a lintable."""
        return f"{self.name} ({self.kind})"


# pylint: disable=redefined-outer-name
def discover_lintables(options: Namespace) -> Dict[str, Any]:
    """Find all files that we know how to lint."""
    # git is preferred as it also considers .gitignore
    git_command_present = [
        "git",
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    ]
    git_command_absent = ["git", "ls-files", "--deleted", "-z"]
    out = None

    try:
        out_present = subprocess.check_output(
            git_command_present, stderr=subprocess.STDOUT, universal_newlines=True
        ).split("\x00")[:-1]
        _logger.info(
            "Discovered files to lint using: %s", " ".join(git_command_present)
        )

        out_absent = subprocess.check_output(
            git_command_absent, stderr=subprocess.STDOUT, universal_newlines=True
        ).split("\x00")[:-1]
        _logger.info("Excluded removed files using: %s", " ".join(git_command_absent))

        out = set(out_present) - set(out_absent)
    except subprocess.CalledProcessError as exc:
        if not (exc.returncode == 128 and "fatal: not a git repository" in exc.output):
            _logger.warning(
                "Failed to discover lintable files using git: %s",
                exc.output.rstrip("\n"),
            )
    except FileNotFoundError as exc:
        if options.verbosity:
            _logger.warning("Failed to locate command: %s", exc)

    if out is None:
        exclude_pattern = "|".join(str(x) for x in options.exclude_paths)
        _logger.info("Looking up for files, excluding %s ...", exclude_pattern)
        # remove './' prefix from output of WcMatch
        out = {
            strip_dotslash_prefix(fname)
            for fname in WcMatch(
                ".", exclude_pattern=exclude_pattern, flags=RECURSIVE, limit=256
            ).match()
        }

    return OrderedDict.fromkeys(sorted(out))


def strip_dotslash_prefix(fname: str) -> str:
    """Remove ./ leading from filenames."""
    return fname[2:] if fname.startswith("./") else fname


def guess_project_dir(config_file: Optional[str]) -> str:
    """Return detected project dir or current working directory."""
    path = None
    if config_file is not None:
        target = pathlib.Path(config_file)
        if target.exists():
            path = str(target.parent.absolute())

    if path is None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True,
                check=True,
            )

            path = result.stdout.splitlines()[0]
        except subprocess.CalledProcessError as exc:
            if not (
                exc.returncode == 128 and "fatal: not a git repository" in exc.stderr
            ):
                _logger.warning(
                    "Failed to guess project directory using git: %s",
                    exc.stderr.rstrip("\n"),
                )
        except FileNotFoundError as exc:
            _logger.warning("Failed to locate command: %s", exc)

    if path is None:
        path = os.getcwd()

    _logger.info(
        "Guessed %s as project root directory",
        path,
    )

    return path


def expand_dirs_in_lintables(lintables: Set[Lintable]) -> None:
    """Return all recognized lintables within given directory."""
    should_expand = False

    for item in lintables:
        if item.path.is_dir():
            should_expand = True
            break

    if should_expand:
        # this relies on git and we do not want to call unless needed
        all_files = discover_lintables(options)

        for item in copy.copy(lintables):
            if item.path.is_dir():
                for filename in all_files:
                    if filename.startswith(str(item.path)):
                        lintables.add(Lintable(filename))
