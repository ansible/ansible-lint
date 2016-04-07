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
from collections import defaultdict
import codecs
import errno
import optparse
import os
import sys

from ansiblelint.version import __version__
import ansiblelint.formatters as formatters
import ansiblelint.utils as utils


class AnsibleLintRule(object):

    def __repr__(self):
        return self.id + ": " + self.shortdesc

    def verbose(self):
        return self.id + ": " + self.shortdesc + "\n  " + self.description

    def match(self, file="", line=""):
        return []

    def matchlines(self, file, text):
        matches = []
        # arrays are 0-based, line numbers are 1-based
        # so use prev_line_no as the counter
        for (prev_line_no, line) in enumerate(text.split("\n")):
            result = self.match(file, line)
            if result:
                message = None
                if isinstance(result, str):
                    message = result
                matches.append(Match(prev_line_no+1, line,
                               file['path'], self, message))
        return matches

    def matchtask(self, file="", task=None):
        return []

    def matchtasks(self, file, text):
        matches = []
        yaml = utils.parse_yaml_linenumbers(text)
        if yaml:
            for task in utils.get_action_tasks(yaml, file):
                # An empty `tags` block causes `None` to be returned if
                # the `or []` is not present - `task.get('tags', [])`
                # does not suffice.
                if 'skip_ansible_lint' in (task.get('tags') or []):
                    continue
                if 'action' in task:
                    result = self.matchtask(file, task)
                    if result:
                        message = None
                        if isinstance(result, basestring):
                            message = result
                        taskstr = "Task/Handler: " + utils.task_to_str(task)
                        matches.append(Match(task[utils.LINE_NUMBER_KEY], taskstr,
                                       file['path'], self, message))
        return matches

    def matchyaml(self, file, text):
        matches = []
        yaml = utils.parse_yaml_linenumbers(text)
        if yaml and hasattr(self, 'matchplay'):
            for play in yaml:
                result = self.matchplay(file, play)
                if result:
                    if isinstance(result, tuple):
                        result = [result]

                    if not isinstance(result, list):
                        raise Exception("{} is not a list".format(result))

                    for section, message in result:
                        matches.append(Match(play[utils.LINE_NUMBER_KEY],
                                             section, file['path'], self, message))
        return matches


class RulesCollection(object):

    def __init__(self):
        self.rules = []

    def register(self, obj):
        self.rules.append(obj)

    def __iter__(self):
        return iter(self.rules)

    def __len__(self):
        return len(self.rules)

    def extend(self, more):
        self.rules.extend(more)

    def run(self, playbookfile, tags=set(), skip_list=set()):
        text = ""
        matches = list()

        try:
            with codecs.open(playbookfile['path'], mode='rb', encoding='utf-8') as f:
                text = f.read()
        except IOError, e:
            print("WARNING: Couldn't open %s - %s" %
                  (playbookfile['path'], e.strerror),
                  file=sys.stderr)
            return matches

        for rule in self.rules:
            if not tags or not set(rule.tags).union([rule.id]).isdisjoint(tags):
                rule_definition = set(rule.tags)
                rule_definition.add(rule.id)
                if set(rule_definition).isdisjoint(skip_list):
                    matches.extend(rule.matchlines(playbookfile, text))
                    matches.extend(rule.matchtasks(playbookfile, text))
                    matches.extend(rule.matchyaml(playbookfile, text))

        return matches

    def __repr__(self):
        return "\n".join([rule.verbose()
                          for rule in sorted(self.rules, key=lambda x: x.id)])

    def listtags(self):
        tags = defaultdict(list)
        for rule in self.rules:
            for tag in rule.tags:
                tags[tag].append("[{0}]".format(rule.id))
        results = []
        for tag in sorted(tags):
            results.append("{0} {1}".format(tag, tags[tag]))
        return "\n".join(results)

    @classmethod
    def create_from_directory(cls, rulesdir):
        result = cls()
        result.rules = utils.load_plugins(os.path.expanduser(rulesdir))
        return result


class Match(object):

    def __init__(self, linenumber, line, filename, rule, message=None):
        self.linenumber = linenumber
        self.line = line
        self.filename = filename
        self.rule = rule
        self.message = message or rule.shortdesc

    def __repr__(self):
        formatstr = u"[{0}] ({1}) matched {2}:{3} {4}"
        return formatstr.format(self.rule.id, self.message,
                                self.filename, self.linenumber, self.line)


class Runner(object):

    def __init__(self, rules, playbooks, tags, skip_list, exclude_paths):
        self.rules = rules
        self.playbooks = set()
        for pb in playbooks:
            self.playbooks.add((pb, 'playbook'))
        self.tags = tags
        self.skip_list = skip_list
        self._update_exclude_paths(exclude_paths)

    def _update_exclude_paths(self, exclude_paths):
        if exclude_paths:
            # These will be (potentially) relative paths
            paths = [s.strip() for s in exclude_paths]
            # Since utils.find_children returns absolute paths,
            # and the list of files we create in `Runner.run` can contain both
            # relative and absolute paths, we need to cover both bases.
            self.exclude_paths = paths + [os.path.abspath(p) for p in paths]
        else:
            self.exclude_paths = []

    def is_excluded(self, file_path):
        # Any will short-circuit as soon as something returns True, but will
        # be poor performance for the case where the path under question is
        # not excluded.
        return any(file_path.startswith(path) for path in self.exclude_paths)

    def run(self):
        files = list()
        for playbook in self.playbooks:
            if self.is_excluded(playbook[0]):
                continue
            files.append({'path': playbook[0], 'type': playbook[1]})
        visited = set()
        while (visited != self.playbooks):
            for arg in self.playbooks - visited:
                for file in utils.find_children(arg):
                    if self.is_excluded(file['path']):
                        continue
                    self.playbooks.add((file['path'], file['type']))
                    files.append(file)
                visited.add(arg)

        matches = list()
        for file in files:
            matches.extend(self.rules.run(file, tags=set(self.tags),
                           skip_list=set(self.skip_list)))

        return matches

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    #try:
    #    cmd_name, cmd_args = parseopts(args)
    #except Exception as exc:
    #    sys.stderr.write("ERROR: %s" % exc)
    #    sys.stderr.write(os.linesep)
    #    sys.exit(1)

    # Needed for locale.getpreferredencoding(False) to work
    # in pip.utils.encoding.auto_decode
    #try:
    #    locale.setlocale(locale.LC_ALL, '')
    #except locale.Error as e:
    #    # setlocale can apparently crash if locale are uninitialized
    #    logger.debug("Ignoring error %s when setting locale", e)
    #command = commands_dict[cmd_name](isolated=check_isolated(cmd_args))
    #return command.main(cmd_args)


    formatter = formatters.Formatter()

    parser = optparse.OptionParser("%prog playbook.yml",
                                   version="%prog " + __version__)

    default_rulesdir = [os.path.join(os.path.dirname(utils.__file__), 'rules')]

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
                           % default_rulesdir)
    parser.add_option('-R', action='store_true', default=False,
                      dest='use_default_rules',
                      help="Use default rules %s in addition to any extra "
                           "rules directories specified with -r. There is "
                           "no need to specify this if no -r flags are used"
                           % default_rulesdir)
    parser.add_option('-t', dest='tags', default=[],
                      help="only check rules whose id/tags match these values")
    parser.add_option('-T', dest='listtags', action='store_true',
                      help="list all the tags")
    parser.add_option('-x', dest='skip_list', default=[],
                      help="only check rules whose id/tags do not " +
                      "match these values")
    parser.add_option('--exclude', dest='exclude_paths', action='append',
                      help='path to directories or files to skip. This option'
                           ' is repeatable.')
    options, args = parser.parse_args(args)

    if options.quiet:
        formatter = formatters.QuietFormatter()

    if options.parseable:
        formatter = formatters.ParseableFormatter()

    if len(args) == 0 and not (options.listrules or options.listtags):
        parser.print_help(file=sys.stderr)
        return 1

    if options.use_default_rules:
        rulesdirs = options.rulesdir + default_rulesdir
    else:
        rulesdirs = options.rulesdir or default_rulesdir

    rules = RulesCollection()
    for rulesdir in rulesdirs:
        rules.extend(RulesCollection.create_from_directory(rulesdir))

    if options.listrules:
        print(rules)
        return 0

    if options.listtags:
        print(rules.listtags())
        return 0

    if isinstance(options.tags, basestring):
        options.tags = options.tags.split(',')
    if isinstance(options.skip_list, basestring):
        options.skip_list = options.skip_list.split(',')

    playbooks = set(args)
    runner = Runner(rules, playbooks, options.tags,
                                options.skip_list, options.exclude_paths)
    matches = runner.run()

    for match in matches:
        print(formatter.format(match))

    if len(matches):
        return 2
    else:
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except IOError as exc:
        if exc.errno != errno.EPIPE:
            raise
    except RuntimeError as e:
        raise SystemExit(str(e))
