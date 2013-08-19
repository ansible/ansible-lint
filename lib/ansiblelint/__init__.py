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

    @classmethod
    def create_from_directory(cls, rulesdir):
        result = cls()
        result.rules = utils.load_plugins(rulesdir)
        return result
