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
import argparse
import sys

import ansiblelint.formatters as formatters
import six
from ansiblelint import default_rulesdir, RulesCollection, Runner
from ansiblelint.version import __version__
from ansiblelint.utils import get_playbooks_and_roles, normpath
import yaml
import os


def load_config(config_file):
    config_path = config_file if config_file else ".ansible-lint"

    if os.path.exists(config_path):
        with open(config_path, "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError:
                pass

    return None


def main():

    formatter = formatters.Formatter()

    parser = argparse.ArgumentParser()

    parser.add_argument('-L', dest='listrules', default=False,
                        action='store_true', help="list all the rules")
    parser.add_argument('-q', dest='quiet',
                        default=False,
                        action='store_true',
                        help="quieter, although not silent output")
    parser.add_argument('-p', dest='parseable',
                        default=False,
                        action='store_true',
                        help="parseable output in the format of pep8")
    parser.add_argument('--parseable-severity', dest='parseable_severity',
                        default=False,
                        action='store_true',
                        help="parseable output including severity of rule")
    parser.add_argument('-r', action='append', dest='rulesdir',
                        default=[],
                        help="specify one or more rules directories using "
                             "one or more -r arguments. Any -r flags override "
                             "the default rules in %s, unless -R is also used."
                             % default_rulesdir)
    parser.add_argument('-R', action='store_true',
                        default=False,
                        dest='use_default_rules',
                        help="Use default rules in %s in addition to any extra "
                             "rules directories specified with -r. There is "
                             "no need to specify this if no -r flags are used"
                             % default_rulesdir)
    parser.add_argument('-t', dest='tags',
                        action='append',
                        default=[],
                        help="only check rules whose id/tags match these values")
    parser.add_argument('-T', dest='listtags', action='store_true',
                        help="list all the tags")
    parser.add_argument('-v', dest='verbosity', action='count',
                        help="Increase verbosity level",
                        default=0)
    parser.add_argument('-x', dest='skip_list', default=[], action='append',
                        help="only check rules whose id/tags do not " +
                        "match these values")
    parser.add_argument('--nocolor', dest='colored',
                        default=hasattr(sys.stdout, 'isatty') and sys.stdout.isatty(),
                        action='store_false',
                        help="disable colored output")
    parser.add_argument('--force-color', dest='colored',
                        action='store_true',
                        help="Try force colored output (relying on ansible's code)")
    parser.add_argument('--exclude', dest='exclude_paths', action='append',
                        help='path to directories or files to skip. This option'
                             ' is repeatable.',
                        default=[])
    parser.add_argument('-c', dest='config_file',
                        help='Specify configuration file to use.  '
                             'Defaults to ".ansible-lint"')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('playbook', nargs='*')
    options = parser.parse_args()

    config = load_config(options.config_file)

    if config:
        if 'quiet' in config:
            options.quiet = options.quiet or config['quiet']

        if 'parseable' in config:
            options.parseable = options.parseable or config['parseable']

        if 'parseable_severity' in config:
            options.parseable_severity = options.parseable_severity or \
                config['parseable_severity']

        if 'use_default_rules' in config:
            options.use_default_rules = options.use_default_rules or config['use_default_rules']

        if 'verbosity' in config:
            options.verbosity = options.verbosity + config['verbosity']

        options.exclude_paths.extend(
            config.get('exclude_paths', []))

        if 'rulesdir' in config:
            options.rulesdir = options.rulesdir + config['rulesdir']

        if 'skip_list' in config:
            options.skip_list = options.skip_list + config['skip_list']

        if 'tags' in config:
            options.tags = options.tags + config['tags']

    if options.quiet:
        formatter = formatters.QuietFormatter()

    if options.parseable:
        formatter = formatters.ParseableFormatter()

    if options.parseable_severity:
        formatter = formatters.ParseableSeverityFormatter()

    # no args triggers auto-detection mode
    if not options.playbook and not (options.listrules or options.listtags):
        args = get_playbooks_and_roles(options=options)

    if options.use_default_rules:
        rulesdirs = options.rulesdir + [default_rulesdir]
    else:
        rulesdirs = options.rulesdir or [default_rulesdir]

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

    skip = set()
    for s in options.skip_list:
        skip.update(str(s).split(','))
    options.skip_list = frozenset(skip)

    playbooks = sorted(set(options.playbook or args))

    matches = list()
    checked_files = set()
    for playbook in playbooks:
        runner = Runner(rules, playbook, options.tags,
                        options.skip_list, options.exclude_paths,
                        options.verbosity, checked_files)
        matches.extend(runner.run())

    matches.sort(key=lambda x: (normpath(x.filename), x.linenumber, x.rule.id))

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
