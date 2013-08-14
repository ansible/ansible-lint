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

    rulesInstance = []

    @classmethod
    def getInstance(cls):
        return cls.rulesInstance

    @classmethod
    def register(cls,obj):
        cls.rulesInstance.append(obj)

    @classmethod
    def resetInstance(cls):
        cls.rulesInstance = []
