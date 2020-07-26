from typing import TYPE_CHECKING, List

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import TargetFile


class UnsetVariableMatcherRule(AnsibleLintRule):
    id = 'TEST0002'
    shortdesc = 'Line contains untemplated variable'
    description = 'This is a test rule that looks for lines ' + \
                  'post templating that still contain {{'
    tags = {'fake', 'dummy', 'test2'}

    def match(self, file: "TargetFile", line: str = "") -> List["MatchError"]:
        return "{{" in line
