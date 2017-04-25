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

from __future__ import print_function

import errno
import optparse
import sys

import ansiblelint
import ansiblelint.formatters as formatters
import six
from ansiblelint import RulesCollection
from ansiblelint.version import __version__


def main():

    formatter = formatters.Formatter()

    parser = optparse.OptionParser("%prog playbook.yml",
                                   version="%prog " + __version__)

    parser.add_option('-L', dest='listrules', default=False,
                      action='store_true', help="list all the rules")
    parser.add_option('-q', dest='quiet', default=False, action='store_true',
                      help="quieter, although not silent output")
    parser.add_option('-p', dest='parseable',
                      default=False, action='store_true',
                      help="parseable output in the format of pep8")
    parser.add_option('-r', action='append', dest='rulesdir',
                      default=[], type='str',
                      help="specify one or more rules directories using "
                           "one or more -r arguments. Any -r flags override "
                           "the default rules in %s, unless -R is also used."
                           % ansiblelint.default_rulesdir)
    parser.add_option('-R', action='store_true', default=False,
                      dest='use_default_rules',
                      help="Use default rules in %s in addition to any extra "
                           "rules directories specified with -r. There is "
                           "no need to specify this if no -r flags are used"
                           % ansiblelint.default_rulesdir)
    parser.add_option('-t', dest='tags', default=[],
                      help="only check rules whose id/tags match these values")
    parser.add_option('-T', dest='listtags', action='store_true',
                      help="list all the tags")
    parser.add_option('-v', dest='verbosity', action='count',
                      help="Increase verbosity level", default=0)
    parser.add_option('-x', dest='skip_list', default=[],
                      help="only check rules whose id/tags do not " +
                      "match these values")
    parser.add_option('--nocolor', dest='colored',
                      default=hasattr(sys.stdout, 'isatty') and sys.stdout.isatty(),
                      action='store_false',
                      help="disable colored output")
    parser.add_option('--force-color', dest='colored',
                      action='store_true',
                      help="Try force colored output (relying on ansible's code)")
    parser.add_option('--exclude', dest='exclude_paths', action='append',
                      help='path to directories or files to skip. This option'
                           ' is repeatable.')
    options, args = parser.parse_args(sys.argv[1:])

    if options.quiet:
        formatter = formatters.QuietFormatter()

    if options.parseable:
        formatter = formatters.ParseableFormatter()

    if len(args) == 0 and not (options.listrules or options.listtags):
        parser.print_help(file=sys.stderr)
        return 1

    if options.use_default_rules:
        rulesdirs = options.rulesdir + [ansiblelint.default_rulesdir]
    else:
        rulesdirs = options.rulesdir or [ansiblelint.default_rulesdir]

    rules = RulesCollection()
    for rulesdir in rulesdirs:
        rules.extend(RulesCollection.create_from_directory(rulesdir))

    if options.listrules:
        print(rules)
        return 0

    if options.listtags:
        print(rules.listtags())
        return 0

    if isinstance(options.tags, six.string_types):
        options.tags = options.tags.split(',')
    if isinstance(options.skip_list, six.string_types):
        options.skip_list = options.skip_list.split(',')

    playbooks = set(args)
    matches = list()
    checked_files = set()
    for playbook in playbooks:
        runner = ansiblelint.Runner(rules, playbook, options.tags,
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
