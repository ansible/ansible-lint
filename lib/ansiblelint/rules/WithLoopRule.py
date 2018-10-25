# Copyright (c) 2018, Ansible Project

from ansiblelint import AnsibleLintRule


class WithLoopRule(AnsibleLintRule):
    id = '105'
    shortdesc = 'Deprecated with_X for loops'
    description = """With the release of Ansible 2.5, the recommended way to
    perform loops is to use the new loop keyword instead of with_X style loops
    For more details see:
     https://docs.ansible.com/ansible/2.6/porting_guides/porting_guide_2.5.html
    """
    tags = ['deprecated']

    def matchtask(self, file, task):
        return any(s.startswith('with_') for s in task.keys())
