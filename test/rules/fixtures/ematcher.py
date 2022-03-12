from ansiblelint.rules import AnsibleLintRule


class EMatcherRule(AnsibleLintRule):
    """This is a test custom rule that looks for lines containing BANNED string."""

    id = "TEST0001"
    description = __doc__
    shortdesc = "BANNED string found"
    tags = ["fake", "dummy", "test1"]

    def match(self, line: str) -> bool:
        return "BANNED" in line
