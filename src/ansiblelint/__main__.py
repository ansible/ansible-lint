#!/usr/bin/env python
# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Command line implementation."""

from __future__ import annotations

import errno
import logging
import os
import pathlib
import shutil
import site
import subprocess
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Iterator, TextIO

from ansible_compat.config import ansible_version
from ansible_compat.prerun import get_cache_dir
from filelock import FileLock, Timeout

from ansiblelint import cli
from ansiblelint._mockings import _perform_mockings_cleanup
from ansiblelint.app import get_app
from ansiblelint.color import (
    console,
    console_options,
    console_stderr,
    reconfigure,
    render_yaml,
)
from ansiblelint.config import get_version_warning, options
from ansiblelint.constants import EXIT_CONTROL_C_RC, LOCK_TIMEOUT_RC
from ansiblelint.file_utils import abspath, cwd, normpath
from ansiblelint.skip_utils import normalize_tag
from ansiblelint.version import __version__

if TYPE_CHECKING:
    from argparse import Namespace

    # RulesCollection must be imported lazily or ansible gets imported too early.
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import LintResult


_logger = logging.getLogger(__name__)


def initialize_logger(level: int = 0) -> None:
    """Set up the global logging level based on the verbosity number."""
    # We are about to act on the root logger, which defaults to logging.WARNING.
    # That is where our 0 (default) value comes from.
    verbosity_map = {
        -2: logging.CRITICAL,
        -1: logging.ERROR,
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    # Unknown logging level is treated as DEBUG
    logging_level = verbosity_map.get(level, logging.DEBUG)
    logger.setLevel(logging_level)
    logging.captureWarnings(True)  # pass all warnings.warn() messages through logging
    # Use module-level _logger instance to validate it
    _logger.debug("Logging initialized to level %s", logging_level)


def initialize_options(arguments: list[str] | None = None) -> None:
    """Load config options and store them inside options module."""
    new_options = cli.get_config(arguments or [])
    new_options.cwd = pathlib.Path.cwd()

    if new_options.colored is None:
        new_options.colored = should_do_markup()

    # persist loaded configuration inside options module
    for k, v in new_options.__dict__.items():
        setattr(options, k, v)

    # rename deprecated ids/tags to newer names
    options.tags = [normalize_tag(tag) for tag in options.tags]
    options.skip_list = [normalize_tag(tag) for tag in options.skip_list]
    options.warn_list = [normalize_tag(tag) for tag in options.warn_list]

    options.configured = True
    options.cache_dir = get_cache_dir(options.project_dir)

    # add a lock file so we do not have two instances running inside at the same time
    os.makedirs(options.cache_dir, exist_ok=True)

    options.cache_dir_lock = None
    if not options.offline:
        options.cache_dir_lock = FileLock(f"{options.cache_dir}/.lock")
        try:
            options.cache_dir_lock.acquire(timeout=180)
        except Timeout:  # pragma: no cover
            _logger.error(
                "Timeout waiting for another instance of ansible-lint to release the lock."
            )
            sys.exit(LOCK_TIMEOUT_RC)

    # Avoid extra output noise from Ansible about using devel versions
    if "ANSIBLE_DEVEL_WARNING" not in os.environ:  # pragma: no branch
        os.environ["ANSIBLE_DEVEL_WARNING"] = "false"


def _do_list(rules: RulesCollection) -> int:
    # On purpose lazy-imports to avoid pre-loading Ansible
    # pylint: disable=import-outside-toplevel
    from ansiblelint.generate_docs import (
        rules_as_docs,
        rules_as_md,
        rules_as_rich,
        rules_as_str,
    )

    if options.list_rules:

        _rule_format_map: dict[str, Callable[..., Any]] = {
            "plain": rules_as_str,
            "rich": rules_as_rich,
            "md": rules_as_md,
            "docs": rules_as_docs,
        }

        console.print(_rule_format_map[options.format](rules), highlight=False)
        return 0

    if options.list_tags:
        console.print(render_yaml(rules.list_tags()))
        return 0

    # we should not get here!
    return 1


# noinspection PyShadowingNames
def _do_transform(result: LintResult, opts: Namespace) -> None:
    """Create and run Transformer."""
    if "yaml" in opts.skip_list:
        # The transformer rewrites yaml files, but the user requested to skip
        # the yaml rule or anything tagged with "yaml", so there is nothing to do.
        return

    # On purpose lazy-imports to avoid loading transforms unless requested
    # pylint: disable=import-outside-toplevel
    from ansiblelint.transformer import Transformer

    transformer = Transformer(result, options)

    # this will mark any matches as fixed if the transforms repaired the issue
    transformer.run()


def support_banner() -> None:
    """Display support banner when running on unsupported platform."""
    if sys.version_info < (3, 9, 0):
        prefix = "::warning::" if "GITHUB_ACTION" in os.environ else "WARNING: "
        console_stderr.print(
            f"{prefix}ansible-lint is no longer tested under Python {sys.version_info.major}.{sys.version_info.minor} and will soon require 3.9. Do not report bugs for this version.",
            style="bold red",
        )


# pylint: disable=too-many-branches,too-many-statements
def main(argv: list[str] | None = None) -> int:  # noqa: C901
    """Linter CLI entry point."""
    # alter PATH if needed (venv support)
    path_inject()

    if argv is None:
        argv = sys.argv
    initialize_options(argv[1:])

    console_options["force_terminal"] = options.colored
    reconfigure(console_options)

    if options.version:
        console.print(
            f"ansible-lint [repr.number]{__version__}[/] using ansible [repr.number]{ansible_version()}[/]"
        )
        msg = get_version_warning()
        if msg:
            console.print(msg)
        support_banner()
        sys.exit(0)
    else:
        support_banner()

    initialize_logger(options.verbosity)
    _logger.debug("Options: %s", options)
    _logger.debug(os.getcwd())

    if not options.offline:
        # refresh schemas must happen before loading rules
        if "ansiblelint.schemas" in sys.modules:
            raise RuntimeError("ansiblelint.schemas should not be loaded yet")
        # pylint: disable=import-outside-toplevel
        from ansiblelint.schemas import refresh_schemas

        refresh_schemas()

    # pylint: disable=import-outside-toplevel
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import _get_matches

    rules = RulesCollection(options.rulesdirs, profile_name=options.profile)

    if options.list_profiles:
        from ansiblelint.generate_docs import profiles_as_rich

        console.print(profiles_as_rich())
        return 0

    if options.list_rules or options.list_tags:
        return _do_list(rules)

    app = get_app()
    if isinstance(options.tags, str):
        options.tags = options.tags.split(",")
    result = _get_matches(rules, options)

    if options.write_list:
        _do_transform(result, options)

    mark_as_success = True
    if result.matches and options.progressive:
        mark_as_success = False
        _logger.info(
            "Matches found, running again on previous revision in order to detect regressions"
        )
        with _previous_revision():
            _logger.debug("Options: %s", options)
            _logger.debug(os.getcwd())
            old_result = _get_matches(rules, options)
            # remove old matches from current list
            matches_delta = list(set(result.matches) - set(old_result.matches))
            if len(matches_delta) == 0:
                _logger.warning(
                    "Total violations not increased since previous "
                    "commit, will mark result as success. (%s -> %s)",
                    len(old_result.matches),
                    len(matches_delta),
                )
                mark_as_success = True

            ignored = 0
            for match in result.matches:
                # if match is not new, mark is as ignored
                if match not in matches_delta:
                    match.ignored = True
                    ignored += 1
            if ignored:
                _logger.warning(
                    "Marked %s previously known violation(s) as ignored due to"
                    " progressive mode.",
                    ignored,
                )

    if options.strict and result.matches:
        mark_as_success = False

    app.render_matches(result.matches)

    _perform_mockings_cleanup()
    if options.cache_dir_lock:
        options.cache_dir_lock.release()
        pathlib.Path(options.cache_dir_lock.lock_file).unlink(missing_ok=True)
    if options.mock_filters:
        _logger.warning(
            "The following filters were mocked during the run: %s",
            ",".join(options.mock_filters),
        )

    return app.report_outcome(result, mark_as_success=mark_as_success)


@contextmanager
def _previous_revision() -> Iterator[None]:
    """Create or update a temporary workdir containing the previous revision."""
    worktree_dir = f"{options.cache_dir}/old-rev"
    # Update options.exclude_paths to include use the temporary workdir.
    rel_exclude_paths = [normpath(p) for p in options.exclude_paths]
    options.exclude_paths = [abspath(p, worktree_dir) for p in rel_exclude_paths]
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD^1"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout.strip()
    _logger.info("Previous revision SHA: %s", revision)
    path = pathlib.Path(worktree_dir)
    if path.exists():
        shutil.rmtree(worktree_dir)
    path.mkdir(parents=True, exist_ok=True)
    # Run check will fail if worktree_dir already exists
    # pylint: disable=subprocess-run-check
    subprocess.run(
        ["git", "worktree", "add", "-f", worktree_dir],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        with cwd(worktree_dir):
            subprocess.run(
                ["git", "checkout", revision],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            yield
    finally:
        options.exclude_paths = [abspath(p, os.getcwd()) for p in rel_exclude_paths]


def _run_cli_entrypoint() -> None:
    """Invoke the main entrypoint with current CLI args.

    This function also processes the runtime exceptions.
    """
    try:
        sys.exit(main(sys.argv))
    except OSError as exc:
        # NOTE: Only "broken pipe" is acceptable to ignore
        if exc.errno != errno.EPIPE:  # pragma: no cover
            raise
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(EXIT_CONTROL_C_RC)
    except RuntimeError as exc:  # pragma: no cover
        raise SystemExit(exc) from exc


def path_inject() -> None:
    """Add python interpreter path to top of PATH to fix outside venv calling."""
    # This make it possible to call ansible-lint that was installed inside a
    # virtualenv without having to pre-activate it. Otherwise subprocess will
    # either fail to find ansible executables or call the wrong ones.
    #
    # This must be run before we do run any subprocesses, and loading config
    # does this as part of the ansible detection.
    paths = [x for x in os.environ.get("PATH", "").split(os.pathsep) if x]

    # Expand ~ in PATH as it known to break many tools
    expanded = False
    for idx, path in enumerate(paths):
        if "~" in path:
            paths[idx] = os.path.expanduser(path)
            expanded = True
    if expanded:
        print(
            "WARNING: PATH altered to expand ~ in it. Read https://stackoverflow.com/a/44704799/99834 and correct your system configuration.",
            file=sys.stderr,
        )

    inject_paths = []

    userbase_bin_path = f"{site.getuserbase()}/bin"
    if userbase_bin_path not in paths and os.path.exists(
        f"{userbase_bin_path}/bin/ansible"
    ):
        inject_paths.append(userbase_bin_path)

    py_path = os.path.dirname(sys.executable)
    if py_path not in paths and os.path.exists(f"{py_path}/ansible"):
        inject_paths.append(py_path)

    if inject_paths:
        print(
            f"WARNING: PATH altered to include {', '.join(inject_paths)} :: This is usually a sign of broken local setup, which can cause unexpected behaviors.",
            file=sys.stderr,
        )
    if inject_paths or expanded:
        os.environ["PATH"] = os.pathsep.join([*inject_paths, *paths])

    # We do know that finding ansible in PATH does not guarantee that it is
    # functioning or that is in fact the same version that was installed as
    # our dependency, but addressing this would be done by ansible-compat.
    if not shutil.which("ansible"):
        raise RuntimeError("Failed to find ansible executable in PATH")


# Based on Ansible implementation
def to_bool(value: Any) -> bool:
    """Return a bool for the arg."""
    if value is None or isinstance(value, bool):
        return bool(value)
    if isinstance(value, str):
        value = value.lower()
    if value in ("yes", "on", "1", "true", 1):
        return True
    return False


def should_do_markup(stream: TextIO = sys.stdout) -> bool:  # pragma: no cover
    """Decide about use of ANSI colors."""
    py_colors = None

    # https://xkcd.com/927/
    for env_var in ["PY_COLORS", "CLICOLOR", "FORCE_COLOR", "ANSIBLE_FORCE_COLOR"]:
        value = os.environ.get(env_var, None)
        if value is not None:
            py_colors = to_bool(value)
            break

    # If deliberately disabled colors
    if os.environ.get("NO_COLOR", None):
        return False

    # User configuration requested colors
    if py_colors is not None:
        return to_bool(py_colors)

    term = os.environ.get("TERM", "")
    if "xterm" in term:
        return True

    if term == "dumb":
        return False

    # Use tty detection logic as last resort because there are numerous
    # factors that can make isatty return a misleading value, including:
    # - stdin.isatty() is the only one returning true, even on a real terminal
    # - stderr returning false if user user uses a error stream coloring solution
    return stream.isatty()


if __name__ == "__main__":
    _run_cli_entrypoint()
