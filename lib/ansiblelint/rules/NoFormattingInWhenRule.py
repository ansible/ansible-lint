from ansiblelint import AnsibleLintRule


class NoFormattingInWhenRule(AnsibleLintRule):
    id = 'CINCH0001'
    shortdesc = 'No Jinja2 in when'
    description = '"when" lines should not include Jinja2 variables'
    tags = ['deprecated']

    def matchtask(self, file, task):
        return 'when' in task and \
                isinstance(task['when'], (str, unicode)) and \
                (task['when'].find('{{') != -1 or
                 task['when'].find('}}') != -1)
