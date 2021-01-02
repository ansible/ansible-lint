from typing import List

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule


class SudoRule(AnsibleLintRule):
    id = '103'
    shortdesc = 'Deprecated sudo'
    description = 'Instead of ``sudo``/``sudo_user``, use ``become``/``become_user``.'
    severity = 'VERY_HIGH'
    tags = ['deprecations']
    version_added = 'historic'

    def _check_value(self, play_frag) -> List[MatchError]:
        results = []

        if isinstance(play_frag, dict):
            if 'sudo' in play_frag:
                results.append(
                    self.create_matcherror(
                        message='Deprecated sudo feature',
                        linenumber=play_frag['__line__']
                    ))
            if 'sudo_user' in play_frag:
                results.append(
                    self.create_matcherror(
                        message='Deprecated sudo_user feature',
                        linenumber=play_frag['__line__']))
            if 'tasks' in play_frag:
                output = self._check_value(play_frag['tasks'])
                if output:
                    results += output

        if isinstance(play_frag, list):
            for item in play_frag:
                output = self._check_value(item)
                if output:
                    results += output

        return results

    def matchplay(self, file: Lintable, data) -> List[MatchError]:
        return self._check_value(data)
