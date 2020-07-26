from typing import TYPE_CHECKING, List

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import TargetFile


class EMatcherRule(AnsibleLintRule):
    id = 'TEST0001'
    description = 'This is a test rule that looks for lines ' + \
                  'containing the letter e'
    shortdesc = 'The letter "e" is present'
    tags = {'fake', 'dummy', 'test1'}

    def match(self, file: "TargetFile", line: str = "") -> List["MatchError"]:
        return "e" in line
