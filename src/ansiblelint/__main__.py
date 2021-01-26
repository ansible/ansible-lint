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
import subprocess
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, List

from enrich.console import should_do_markup

from ansiblelint import cli
from ansiblelint._prerun import check_ansible_presence, prepare_environment
from ansiblelint.app import App
from ansiblelint.color import console, console_options, console_stderr, reconfigure, render_yaml
from ansiblelint.config import options
from ansiblelint.file_utils import cwd
from ansiblelint.version import __version__

if TYPE_CHECKING:
    from ansiblelint.runner import LintResult


_logger = logging.getLogger(__name__)


def initialize_logger(level: int = 0) -> None:
    """Set up the global logging level based on the verbosity number."""
    VERBOSITY_MAP = {
        0: logging.NOTSET,
        1: logging.INFO,
        2: logging.DEBUG
    }

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger(__package__)
    logger.addHandler(handler)
    # Unknown logging level is treated as DEBUG
    logging_level = VERBOSITY_MAP.get(level, logging.DEBUG)
    logger.setLevel(logging_level)
    # Use module-level _logger instance to validate it
    _logger.debug("Logging initialized to level %s", logging_level)


def initialize_options(arguments: List[str]):
    """Load config options and store them inside options module."""
    new_options = cli.get_config(arguments)
    new_options.cwd = pathlib.Path.cwd()

    if new_options.version:
        print('ansible-lint {ver!s}'.format(ver=__version__))
        # assure we fail if ansible is missing, even for version printing
        check_ansible_presence()
        sys.exit(0)

    if new_options.colored is None:
        new_options.colored = should_do_markup()

    # persist loaded configuration inside options module
    for k, v in new_options.__dict__.items():
        setattr(options, k, v)


def report_outcome(result: "LintResult", options, mark_as_success=False) -> int:
    """Display information about how to skip found rules.

    Returns exit code, 2 if errors were found, 0 when only warnings were found.
    """
    failures = 0
    warnings = 0
    msg = """\
# .ansible-lint
warn_list:  # or 'skip_list' to silence them completely
"""
    matches_unignored = [match for match in result.matches if not match.ignored]

    # counting
    matched_rules = {match.rule.id: match.rule for match in matches_unignored}
    for match in result.matches:
        if {match.rule.id, *match.rule.tags}.isdisjoint(options.warn_list):
            failures += 1
        else:
            warnings += 1

    for key in sorted(matched_rules.keys()):
        if {key, *matched_rules[key].tags}.isdisjoint(options.warn_list):
            msg += f"  - '{key}'  # {matched_rules[key].shortdesc}\n"
    for match in result.matches:
        if "experimental" in match.rule.tags:
            msg += "  - experimental  # all rules tagged as experimental\n"
            break

    if result.matches and not options.quiet:
        console_stderr.print(
            "You can skip specific rules or tags by adding them to your "
            "configuration file:")
        console_stderr.print(render_yaml(msg))
        console_stderr.print(
            f"Finished with {failures} failure(s), {warnings} warning(s) "
            f"on {len(result.files)} files."
        )

    if mark_as_success or not failures:
        return 0
    return 2


def main(argv: List[str] = None) -> int:
    """Linter CLI entry point."""
    if argv is None:
        argv = sys.argv
    initialize_options(argv[1:])

    console_options["force_terminal"] = options.colored
    reconfigure(console_options)

    initialize_logger(options.verbosity)
    _logger.debug("Options: %s", options)

    app = App(options=options)

    prepare_environment()
    check_ansible_presence()

    # On purpose lazy-imports to avoid pre-loading Ansible
    # pylint: disable=import-outside-toplevel
    from ansiblelint.generate_docs import rules_as_rich, rules_as_rst
    from ansiblelint.rules import RulesCollection

    rules = RulesCollection(options.rulesdirs)

    if options.listrules:

        _rule_format_map = {
            'plain': str,
            'rich': rules_as_rich,
            'rst': rules_as_rst
        }

        console.print(
            _rule_format_map[options.format](rules),
            highlight=False)
        return 0

    if options.listtags:
        console.print(
            render_yaml(rules.listtags())
            )
        return 0

    if isinstance(options.tags, str):
        options.tags = options.tags.split(',')

    from ansiblelint.runner import _get_matches
    result = _get_matches(rules, options)

    mark_as_success = False
    if result.matches and options.progressive:
        _logger.info(
            "Matches found, running again on previous revision in order to detect regressions")
        with _previous_revision():
            old_result = _get_matches(rules, options)
            # remove old matches from current list
            matches_delta = list(set(result.matches) - set(old_result.matches))
            if len(matches_delta) == 0:
                _logger.warning(
                    "Total violations not increased since previous "
                    "commit, will mark result as success. (%s -> %s)",
                    len(old_result.matches), len(matches_delta))
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
                    " progressive mode.", ignored)

    app.render_matches(result.matches)

    return report_outcome(result, mark_as_success=mark_as_success, options=options)


@contextmanager
def _previous_revision():
    """Create or update a temporary workdir containing the previous revision."""
    worktree_dir = ".cache/old-rev"
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD^1"],
        check=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        ).stdout
    p = pathlib.Path(worktree_dir)
    p.mkdir(parents=True, exist_ok=True)
    os.system(f"git worktree add -f {worktree_dir} 2>/dev/null")
    with cwd(worktree_dir):
        os.system(f"git checkout {revision}")
        yield


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
    except RuntimeError as e:
        raise SystemExit(str(e))


if __name__ == "__main__":
    _run_cli_entrypoint()
