class AnsibleLintRule(object):

    def __init__(self,
            id=None,
            description="",
            tags=[]):
        self.id = id
        self.description = description
        self.tags = tags

    def prematch(self, playbook=""):
        return []

    def postmatch(self, playbook=""):
        return []


class RulesCollection(object):

    rules = []

    def register(self,obj):
        self.rules.append(obj)

    def __len__(self):
        return len(self.rules)
