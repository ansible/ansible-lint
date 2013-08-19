import ansiblelint.utils

class AnsibleLintRule(object):

    def __init__(self,
            id=None,
            description="",
            tags=[]):
        self.id = id
        self.description = description
        self.tags = tags

    def __repr__(self):
        return self.id + ": " + self.description

    def prematch(self, playbook=""):
        return []

    def postmatch(self, playbook=""):
        return []


class RulesCollection(object):

    def __init__(self):
        self.rules = []

    def register(self,obj):
        self.rules.append(obj)

    def __len__(self):
        return len(self.rules)

    def run(self, playbookfile, tags=None, skip_tags=None):
        text = ""
        matches = list()
        with open(playbookfile, 'r') as f:
            text = f.read()
        for rule in self.rules:
            if not tags or rule.tag in tags:
                if not skip_tags or rule.tag not in skip_tags:
                    matches.extend(Match.from_matches(filename, rule, text))
                    matches.extend(rule.postmatch(text))
        return matches

    @classmethod
    def create_from_directory(cls, rulesdir):
        result = cls()
        result.rules = utils.load_plugins(rulesdir)
        return result


class Match:

    def __init__(self, linenumber, line, filename, rule):
        self.linenumber = linenumber
        self.line = line
        self.filename = filename
        self.rule = rule

    def __repr__(self):
        return "[{}] ({}) matched {}:{} {}" % (rule.id, rule.description,
                                               filename, linenumber, line)

    @staticmethod
    def from_matches(filename, rule, text):
        result = list()
        for match in rule.prematch(text).extend(rule.postmatch(text)):
            result.append(match, text.split("\n")[match-1], filename, rule)
        return result
