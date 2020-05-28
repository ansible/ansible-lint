from ansiblelint.rules import AnsibleLintRule


class NoFormattingInWhenRule(AnsibleLintRule):
    id = '102'
    shortdesc = 'No Jinja2 in when'
    description = '``when`` lines should not include Jinja2 variables'
    severity = 'HIGH'
    tags = ['deprecated', 'ANSIBLE0019']
    version_added = 'historic'

    def _is_valid(self, when):
        if not isinstance(when, str):
            return True
        return when.find('{{') == -1 and when.find('}}') == -1

    def matchplay(self, file, play):
        errors = []
        if isinstance(play, dict):
            if 'roles' not in play or play['roles'] is None:
                return errors
            for role in play['roles']:
                if self.matchtask(file, role):
                    errors.append(({'when': role},
                                   'role "when" clause has Jinja2 templates'))
        if isinstance(play, list):
            for play_item in play:
                sub_errors = self.matchplay(file, play_item)
                if sub_errors:
                    errors = errors + sub_errors
        return errors

    def matchtask(self, file, task):
        return 'when' in task and not self._is_valid(task['when'])
