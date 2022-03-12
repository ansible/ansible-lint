from ansiblelint.rules import AnsibleLintRule


class UnsetVariableMatcherRule(AnsibleLintRule):
    """This is a test rule that looks for lines post templating that still contain {{."""

    id = "TEST0002"
    shortdesc = "Line contains untemplated variable"
    description = __doc__
    tags = ["fake", "dummy", "test2"]

    def match(self, line: str) -> bool:
        return "{{" in line
