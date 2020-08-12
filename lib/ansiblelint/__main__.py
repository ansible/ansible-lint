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
import sys
from typing import Any, Set

from ansiblelint import cli, formatters
from ansiblelint.constants import DEFAULT_RULESDIR
from ansiblelint.generate_docs import rules_as_rst
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.utils import get_playbooks_and_roles

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


def main() -> int:
    """Linter CLI entry point."""
    cwd = pathlib.Path.cwd()

    options = cli.get_config(sys.argv[1:])

    initialize_logger(options.verbosity)
    _logger.debug("Options: %s", options)

    formatter_factory: Any = formatters.Formatter
    if options.quiet:
        formatter_factory = formatters.QuietFormatter

    if options.parseable:
        formatter_factory = formatters.ParseableFormatter

    if options.parseable_severity:
        formatter_factory = formatters.ParseableSeverityFormatter

    formatter = formatter_factory(cwd, options.display_relative_path)

    if options.use_default_rules:
        rulesdirs = options.rulesdir + [DEFAULT_RULESDIR]
    else:
        rulesdirs = options.rulesdir or [DEFAULT_RULESDIR]
    rules = RulesCollection(rulesdirs)

    if options.listrules:
        formatted_rules = rules if options.format == 'plain' else rules_as_rst(rules)
        print(formatted_rules)
        return 0

    if options.listtags:
        print(rules.listtags())
        return 0

    if isinstance(options.tags, str):
        options.tags = options.tags.split(',')

    skip = set()
    for s in options.skip_list:
        skip.update(str(s).split(','))
    options.skip_list = frozenset(skip)

    if not options.playbook:
        # no args triggers auto-detection mode
        playbooks = get_playbooks_and_roles(options=options)
    else:
        playbooks = sorted(set(options.playbook))

    matches = list()
    checked_files: Set[str] = set()
    for playbook in playbooks:
        runner = Runner(rules, playbook, options.tags,
                        options.skip_list, options.exclude_paths,
                        options.verbosity, checked_files)
        matches.extend(runner.run())

    # Assure we do not print duplicates and the order is consistent
    matches = sorted(set(matches))

    for match in matches:
        print(formatter.format(match, options.colored))

    # If run under GitHub Actions we also want to emit output recognized by it.
    if os.getenv('GITHUB_ACTIONS') == 'true' and os.getenv('GITHUB_WORKFLOW'):
        formatter = formatters.AnnotationsFormatter(cwd, True)
        for match in matches:
            print(formatter.format(match))

    if matches:
        return 2
    else:
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except IOError as exc:
        if exc.errno != errno.EPIPE:
            raise
    except RuntimeError as e:
        raise SystemExit(str(e))
