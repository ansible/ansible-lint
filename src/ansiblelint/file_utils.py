"""Utility functions related to file operations."""
from __future__ import annotations

import copy
import logging
import os
import subprocess
import sys
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, cast

import wcmatch.pathlib
from wcmatch.wcmatch import RECURSIVE, WcMatch
from yaml.error import YAMLError

from ansiblelint.config import BASE_KINDS, Options, options
from ansiblelint.constants import CONFIG_FILENAMES, GIT_CMD, FileType, States
from ansiblelint.logger import warn_or_fail

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


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


def normpath(path: str | Path) -> str:
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
    if path_absolute.startswith(os.getcwd()):
        return relpath
    if path_absolute.startswith(os.path.expanduser("~")):
        return path_absolute.replace(os.path.expanduser("~"), "~")
    # we avoid returning relative paths that end-up at root level
    if path_absolute in relpath:
        return path_absolute
    if relpath.startswith("../"):
        return path_absolute
    return relpath


# That is needed for compatibility with py38, later was added to Path class
def is_relative_to(path: Path, *other: Any) -> bool:
    """Return True if the path is relative to another path or False."""
    try:
        path.resolve().absolute().relative_to(*other)
        return True
    except ValueError:
        return False


def normpath_path(path: str | Path) -> Path:
    """Normalize a path in order to provide a more consistent output.

    - Any symlinks are resolved.
    - Any paths outside the CWD are resolved to their absolute path.
    - Any absolute path within current user home directory is compressed to
      make use of '~', so it is easier to read and more portable.
    """
    if not isinstance(path, Path):
        path = Path(path)

    is_relative = is_relative_to(path, path.cwd())
    path = path.resolve()
    if is_relative:
        path = path.relative_to(path.cwd())

    # Compress any absolute path within current user home directory
    if path.is_absolute():
        home = Path.home()
        if is_relative_to(path, home):
            path = Path("~") / path.relative_to(home)

    return path


@contextmanager
def cwd(path: str | Path) -> Iterator[None]:
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


def expand_paths_vars(paths: list[str]) -> list[str]:
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
                return str(k)  # type: ignore[return-value]

    if base:
        # Unknown base file type is default
        return ""

    if path.is_dir():
        known_role_subfolders = ("tasks", "meta", "vars", "defaults", "handlers")
        for filename in known_role_subfolders:
            if (path / filename).is_dir():
                return "role"
        _logger.debug(
            "Folder `%s` does not look like a role due to missing any of the common subfolders such: %s.",
            path,
            ", ".join(known_role_subfolders),
        )

    if str(path) == "/dev/stdin":
        return "playbook"

    # Unknown file types report a empty string (evaluated as False)
    return ""


# pylint: disable=too-many-instance-attributes
class Lintable:
    """Defines a file/folder that can be linted.

    Providing file content when creating the object allow creation of in-memory
    instances that do not need files to be present on disk.

    When symlinks are given, they will always be resolved to their target.
    """

    def __init__(
        self,
        name: str | Path,
        content: str | None = None,
        kind: FileType | None = None,
        base_kind: str = "",
    ):
        """Create a Lintable instance."""
        self.dir: str = ""
        self.kind: FileType | None = None
        self.stop_processing = False  # Set to stop other rules from running
        self._data: Any = States.NOT_LOADED
        self.line_skips: dict[int, set[str]] = defaultdict(set)
        self.exc: Exception | None = None  # Stores data loading exceptions

        if isinstance(name, str):
            name = Path(name)
        is_relative = is_relative_to(name, str(name.cwd()))
        name = name.resolve()
        if is_relative:
            name = name.relative_to(name.cwd())
        name = normpath_path(name)
        self.path = name
        # Filename is effective file on disk, for stdin is a namedtempfile
        self.name = self.filename = str(name)

        self._content = self._original_content = content
        self.updated = False

        # if the lintable is part of a role, we save role folder name
        self.role = ""
        parts = self.path.parent.parts
        if "roles" in parts:
            role = self.path
            while role.parent.name != "roles" and role.name:
                role = role.parent
            if role.exists():
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
        self.base_kind = base_kind or kind_from_path(self.path, base=True)
        self.abspath = self.path.expanduser().absolute()

        if self.kind == "yaml":
            _ = self.data  # pylint: disable=pointless-statement

    def _guess_kind(self) -> None:
        if self.kind == "yaml":
            if isinstance(self.data, list) and "hosts" in self.data[0]:
                if "rules" not in self.data[0]:
                    self.kind = "playbook"
                else:
                    self.kind = "rulebook"
            # we we failed to guess the more specific kind, we warn user
            if self.kind == "yaml":
                _logger.debug(
                    "Passed '%s' positional argument was identified as generic '%s' file kind.",
                    self.name,
                    self.kind,
                )

    def __getitem__(self, key: Any) -> Any:
        """Provide compatibility subscriptable support."""
        if key == "path":
            return str(self.path)
        if key == "type":
            return str(self.kind)
        raise NotImplementedError

    def get(self, key: Any, default: Any = None) -> Any:
        """Provide compatibility subscriptable support."""
        try:
            return self[key]
        except NotImplementedError:
            return default

    def _populate_content_cache_from_disk(self) -> None:
        # Can raise UnicodeDecodeError
        self._content = self.path.expanduser().resolve().read_text(encoding="utf-8")

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
            msg = f"Expected str but got {type(value)}"
            raise TypeError(msg)
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
        self.path.expanduser().resolve().write_text(
            self._content or "",
            encoding="utf-8",
        )

    def __hash__(self) -> int:
        """Return a hash value of the lintables."""
        return hash((self.name, self.kind, self.abspath))

    def __eq__(self, other: object) -> bool:
        """Identify whether the other object represents the same rule match."""
        if isinstance(other, Lintable):
            return bool(self.name == other.name and self.kind == other.kind)
        return False

    def __repr__(self) -> str:
        """Return user friendly representation of a lintable."""
        return f"{self.name} ({self.kind})"

    @property
    def data(self) -> Any:
        """Return loaded data representation for current file, if possible."""
        if self._data == States.NOT_LOADED:
            if self.path.is_dir():
                self._data = None
                return self._data
            try:
                if str(self.base_kind) == "text/yaml":
                    from ansiblelint.utils import (  # pylint: disable=import-outside-toplevel
                        parse_yaml_linenumbers,
                    )

                    self._data = parse_yaml_linenumbers(self)
                    # now that _data is not empty, we can try guessing if playbook or rulebook
                    # it has to be done before append_skipped_rules() call as it's relying
                    # on self.kind.
                    if self.kind == "yaml":
                        self._guess_kind()
                    # Lazy import to avoid delays and cyclic-imports
                    if "append_skipped_rules" not in globals():
                        # pylint: disable=import-outside-toplevel
                        from ansiblelint.skip_utils import append_skipped_rules

                    self._data = append_skipped_rules(self._data, self)
                else:
                    logging.debug(
                        "data set to None for %s due to being of %s kind.",
                        self.path,
                        self.base_kind or "unknown",
                    )
                    self._data = States.UNKNOWN_DATA

            except (RuntimeError, FileNotFoundError, YAMLError) as exc:
                self._data = States.LOAD_FAILED
                self.exc = exc
        return self._data


# pylint: disable=redefined-outer-name
def discover_lintables(options: Options) -> dict[str, Any]:
    """Find all files that we know how to lint.

    Return format is normalized, relative for stuff below cwd, ~/ for content
    under current user and absolute for everything else.
    """
    # git is preferred as it also considers .gitignore
    git_command_present = [
        *GIT_CMD,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    ]
    git_command_absent = [*GIT_CMD, "ls-files", "--deleted", "-z"]
    out = None

    try:
        out_present = subprocess.check_output(
            git_command_present,  # noqa: S603
            stderr=subprocess.STDOUT,
            text=True,
        ).split("\x00")[:-1]
        _logger.info(
            "Discovered files to lint using: %s",
            " ".join(git_command_present),
        )

        out_absent = subprocess.check_output(
            git_command_absent,  # noqa: S603
            stderr=subprocess.STDOUT,
            text=True,
        ).split("\x00")[:-1]
        _logger.info("Excluded removed files using: %s", " ".join(git_command_absent))

        out = set(out_present) - set(out_absent)
    except subprocess.CalledProcessError as exc:
        if not (exc.returncode == 128 and "fatal: not a git repository" in exc.output):
            err = exc.output.rstrip("\n")
            warn_or_fail(f"Failed to discover lintable files using git: {err}")
    except FileNotFoundError as exc:
        if options.verbosity:
            warn_or_fail(f"Failed to locate command: {exc}")

    if out is None:
        exclude_pattern = "|".join(str(x) for x in options.exclude_paths)
        _logger.info("Looking up for files, excluding %s ...", exclude_pattern)
        # remove './' prefix from output of WcMatch
        out = {
            strip_dotslash_prefix(fname)
            for fname in WcMatch(
                ".",
                exclude_pattern=exclude_pattern,
                flags=RECURSIVE,
                limit=256,
            ).match()
        }

    return OrderedDict.fromkeys(sorted(out))


def strip_dotslash_prefix(fname: str) -> str:
    """Remove ./ leading from filenames."""
    return fname[2:] if fname.startswith("./") else fname


def find_project_root(
    srcs: Sequence[str],
    config_file: str | None = None,
) -> tuple[Path, str]:
    """Return a directory containing .git or ansible-lint config files.

    That directory will be a common parent of all files and directories
    passed in `srcs`.

    If no directory in the tree contains a marker that would specify it's the
    project root, the root of the file system is returned.

    Returns a two-tuple with the first element as the project root path and
    the second element as a string describing the method by which the
    project root was discovered.
    """
    directory = None
    if not srcs:
        srcs = [str(Path.cwd().resolve().absolute())]
    path_srcs = [Path(Path.cwd(), src).resolve() for src in srcs]

    cfg_files = [config_file] if config_file else CONFIG_FILENAMES

    # A list of lists of parents for each 'src'. 'src' is included as a
    # "parent" of itself if it is a directory
    src_parents = [
        list(path.parents) + ([path] if path.is_dir() else []) for path in path_srcs
    ]

    common_base = max(
        set.intersection(*(set(parents) for parents in src_parents)),
        key=lambda path: path.parts,
    )

    for directory in (common_base, *common_base.parents):
        if (directory / ".git").exists():
            return directory, ".git directory"

        if (directory / ".hg").is_dir():
            return directory, ".hg directory"

        for cfg_file in cfg_files:
            # note that if cfg_file is already absolute, 'directory' is ignored
            resolved_cfg_path = directory / cfg_file
            if resolved_cfg_path.is_file():
                if os.path.isabs(cfg_file):
                    directory = Path(cfg_file).parent
                    if directory.name == ".config":
                        directory = directory.parent
                return directory, f"config file {resolved_cfg_path}"

    if not directory:
        return Path.cwd(), "current working directory"
    return directory, "file system root"


def expand_dirs_in_lintables(lintables: set[Lintable]) -> None:
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
