from typing import List, Optional

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import TargetFile
from ansiblelint.rules import AnsibleLintRule


class UnsetVariableMatcherRule(AnsibleLintRule):
    id = 'TEST0002'
    shortdesc = 'Line contains untemplated variable'
    description = 'This is a test rule that looks for lines ' + \
                  'post templating that still contain {{'
    tags = ['fake', 'dummy', 'test2']

    def match(self, file: TargetFile, line: str, line_no: Optional[int]) -> List[MatchError]:
        if "{{" in line:
            return [self.create_matcherror()]
        return []
