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

import errno
import logging
import os
import pathlib
import shutil
import subprocess
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional

from ansible_compat.config import ansible_version
from ansible_compat.prerun import get_cache_dir
from enrich.console import should_do_markup

from ansiblelint import cli
from ansiblelint.app import get_app
from ansiblelint.color import console, console_options, reconfigure, render_yaml
from ansiblelint.config import options
from ansiblelint.constants import EXIT_CONTROL_C_RC
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


def initialize_options(arguments: Optional[List[str]] = None) -> None:
    """Load config options and store them inside options module."""
    new_options = cli.get_config(arguments or [])
    new_options.cwd = pathlib.Path.cwd()

    if new_options.version:
        print(f"ansible-lint {__version__} using ansible {ansible_version()}")
        sys.exit(0)

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


def _do_list(rules: "RulesCollection") -> int:
    # On purpose lazy-imports to avoid pre-loading Ansible
    # pylint: disable=import-outside-toplevel
    from ansiblelint.generate_docs import rules_as_md, rules_as_rich, rules_as_str

    if options.listrules:

        _rule_format_map: Dict[str, Callable[..., Any]] = {
            "plain": rules_as_str,
            "rich": rules_as_rich,
            "md": rules_as_md,
        }

        console.print(_rule_format_map[options.format](rules), highlight=False)
        return 0

    if options.listtags:
        console.print(render_yaml(rules.listtags()))
        return 0

    # we should not get here!
    return 1


# noinspection PyShadowingNames
def _do_transform(result: "LintResult", opts: "Namespace") -> None:
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


def main(argv: Optional[List[str]] = None) -> int:
    """Linter CLI entry point."""
    # alter PATH if needed (venv support)
    path_inject()

    if argv is None:
        argv = sys.argv
    initialize_options(argv[1:])

    console_options["force_terminal"] = options.colored
    reconfigure(console_options)

    initialize_logger(options.verbosity)
    _logger.debug("Options: %s", options)
    _logger.debug(os.getcwd())

    app = get_app(offline=options.offline)
    # pylint: disable=import-outside-toplevel
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import _get_matches

    rules = RulesCollection(options.rulesdirs)

    if options.listrules or options.listtags:
        return _do_list(rules)

    if isinstance(options.tags, str):
        options.tags = options.tags.split(",")

    result = _get_matches(rules, options)

    if options.write_list:
        _do_transform(result, options)

    mark_as_success = False
    if result.matches and options.progressive:
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

    app.render_matches(result.matches)

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
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout
    path = pathlib.Path(worktree_dir)
    path.mkdir(parents=True, exist_ok=True)
    os.system(f"git worktree add -f {worktree_dir} 2>/dev/null")
    try:
        with cwd(worktree_dir):
            os.system(f"git checkout {revision}")
            yield
    finally:
        options.exclude_paths = [abspath(p, os.getcwd()) for p in rel_exclude_paths]


def _run_cli_entrypoint() -> None:
    """Invoke the main entrypoint with current CLI args.

    This function also processes the runtime exceptions.
    """
    try:
        sys.exit(main(sys.argv))
    except IOError as exc:
        # NOTE: Only "broken pipe" is acceptable to ignore
        if exc.errno != errno.EPIPE:
            raise
    except KeyboardInterrupt:
        sys.exit(EXIT_CONTROL_C_RC)
    except RuntimeError as exc:
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
    ansible_path = shutil.which("ansible")
    if ansible_path:
        ansible_path = os.path.dirname(ansible_path)
    py_path = os.path.dirname(sys.executable)
    # Determine if we need to manipulate PATH
    for path in (ansible_path, py_path):
        if path and path not in paths:  # pragma: no cover
            # tested by test_call_from_outside_venv but coverage cannot detect it
            paths.insert(0, path)
            os.environ["PATH"] = os.pathsep.join(paths)
            print(f"WARNING: PATH altered to include {path}", file=sys.stderr)


if __name__ == "__main__":
    _run_cli_entrypoint()
