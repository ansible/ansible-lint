import ansiblelint.utils

class AnsibleLintRule(object):

    def __repr__(self):
        return self.id + ": " + self.shortdesc

    def verbose(self):
        return self.id + ": " + self.shortdesc + "\n" + self.description


    def match(self, playbook=""):
        return []

    def matchlines(self, filename, text):
        matches = []
        # arrays are 0-based, line numbers are 1-based
        # so use prev_line_no as the counter
        for (prev_line_no, line) in enumerate(text.split("\n")):
            result = self.match(line)
            if result:
                message = None
                if isinstance(result, str):
                    message = result
                matches.append(Match(prev_line_no+1, line, filename, self, message))
        return matches



class RulesCollection(object):

    def __init__(self):
        self.rules = []

    def register(self,obj):
        self.rules.append(obj)

    def __len__(self):
        return len(self.rules)

    def run(self, playbookfile, tags=set(), skip_tags=set()):
        text = ""
        matches = list()
        with open(playbookfile, 'r') as f:
            text = f.read()
        for rule in self.rules:
            if not tags or not rule.tags.isdisjoint(tags):
                if rule.tags.isdisjoint(skip_tags):
                    matches.extend(rule.matchlines(playbookfile, text))

        return matches

    def __repr__(self):
        return "\n".join([rule.verbose() for rule in sorted(self.rules, key = lambda x: x.id)])

    @classmethod
    def create_from_directory(cls, rulesdir):
        result = cls()
        result.rules = utils.load_plugins(rulesdir)
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
