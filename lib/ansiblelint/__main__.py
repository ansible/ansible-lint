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

import errno
import pathlib
import sys

from ansiblelint import cli, RulesCollection, Runner
import ansiblelint.formatters as formatters
from ansiblelint.utils import initialize_logger


def main():
    cwd = pathlib.Path.cwd()

    options = cli.get_config(sys.argv[1:])

    initialize_logger(options.verbosity)

    formatter_factory = formatters.Formatter
    if options.quiet:
        formatter_factory = formatters.QuietFormatter

    if options.parseable:
        formatter_factory = formatters.ParseableFormatter

    if options.parseable_severity:
        formatter_factory = formatters.ParseableSeverityFormatter

    formatter = formatter_factory(cwd, options.display_relative_path)

    rules = RulesCollection(options.rulesdir)

    if options.listrules:
        print(rules)
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

    playbooks = sorted(set(options.playbook))
    matches = list()
    checked_files = set()
    for playbook in playbooks:
        runner = Runner(rules, playbook, options.tags,
                        options.skip_list, options.exclude_paths,
                        options.verbosity, checked_files)
        matches.extend(runner.run())

    matches.sort(key=lambda x: (x.filename, x.linenumber, x.rule.id))

    for match in matches:
        print(formatter.format(match, options.colored))

    if len(matches):
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
