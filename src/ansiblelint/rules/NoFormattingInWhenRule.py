from typing import TYPE_CHECKING, List

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class NoFormattingInWhenRule(AnsibleLintRule):
    id = '102'
    shortdesc = 'No Jinja2 in when'
    description = '``when`` is a raw Jinja2 expression, remove redundant {{ }} from variable(s).'
    severity = 'HIGH'
    tags = ['deprecations']
    version_added = 'historic'

    def _is_valid(self, when):
        if not isinstance(when, str):
            return True
        return when.find('{{') == -1 and when.find('}}') == -1

    def matchplay(self, file: "Lintable", data) -> List["MatchError"]:
        errors: List["MatchError"] = []
        if isinstance(data, dict):
            if 'roles' not in data or data['roles'] is None:
                return errors
            for role in data['roles']:
                if self.matchtask(file, role):  # type: ignore
                    errors.append(
                        self.create_matcherror(details=str({'when': role})))
        if isinstance(data, list):
            for play_item in data:
                sub_errors = self.matchplay(file, play_item)
                if sub_errors:
                    errors = errors + sub_errors
        return errors

    def matchtask(self, file, task):
        return 'when' in task and not self._is_valid(task['when'])
