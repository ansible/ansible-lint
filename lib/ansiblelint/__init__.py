from collections import defaultdict
import os

import ansiblelint.utils
import ansible.utils


class AnsibleLintRule(object):

    def __repr__(self):
        return self.id + ": " + self.shortdesc

    def verbose(self):
        return self.id + ": " + self.shortdesc + "\n" + self.description

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
        yaml = ansible.utils.parse_yaml(text)
        if yaml:
            for task in utils.get_action_tasks(yaml, file):
                result = self.matchtask(file, task)
                if result:
                    message = None
                    if isinstance(result, str):
                        message = result
                    taskstr = "Task/Handler: " + ansiblelint.utils.task_to_str(task)
                    matches.append(Match(0, taskstr,
                                   file['path'], self, message))
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

    def run(self, playbookfile, tags=set(), skip_tags=set()):
        text = ""
        matches = list()
        with open(playbookfile['path'], 'Ur') as f:
            text = f.read()
        for rule in self.rules:
            if not tags or not set(rule.tags).isdisjoint(tags):
                if set(rule.tags).isdisjoint(skip_tags):
                    matches.extend(rule.matchlines(playbookfile, text))
                    matches.extend(rule.matchtasks(playbookfile, text))

        return matches

    def __repr__(self):
        return "\n".join([rule.verbose()
                          for rule in sorted(self.rules, key=lambda x: x.id)])

    def listtags(self):
        tags = defaultdict(list)
        for rule in self.rules:
            for tag in rule.tags:
                tags[tag].append("[{}]".format(rule.id))
        results = []
        for tag in sorted(tags):
            results.append("{} {}".format(tag, tags[tag]))
        return "\n".join(results)

    @classmethod
    def create_from_directory(cls, rulesdir):
        result = cls()
        result.rules = utils.load_plugins(os.path.expanduser(rulesdir))
        return result


class Match:

    def __init__(self, linenumber, line, filename, rule, message=None):
        self.linenumber = linenumber
        self.line = line
        self.filename = filename
        self.rule = rule
        self.message = message or rule.shortdesc

    def __repr__(self):
        formatstr = "[{}] ({}) matched {}:{} {}"
        return formatstr.format(self.rule.id, self.message,
                                self.filename, self.linenumber, self.line)


class Runner:

    def __init__(self, rules, playbooks, tags, skip_tags):
        self.rules = rules
        self.playbooks = playbooks
        self.tags = tags
        self.skip_tags = skip_tags

    def run(self):
        files = list()
        for playbook in self.playbooks:
            files.append({'path': playbook, 'type': 'playbooks'})
        visited = set()
        while (visited != self.playbooks):
            for arg in self.playbooks - visited:
                for file in utils.find_children(arg):
                    self.playbooks.add(file['path'])
                    files.append(file)
                visited.add(arg)

        matches = list()
        for file in files:
            matches.extend(self.rules.run(file, tags=set(self.tags),
                           skip_tags=set(self.skip_tags)))

        return matches
