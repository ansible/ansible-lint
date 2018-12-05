# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project

from ansiblelint import AnsibleLintRule


format = "{}"


class RoleRelativePath(AnsibleLintRule):
    id = '404'
    shortdesc = "Doesn't need a relative path in role"
    description = '``copy`` and ``template`` do not need to use relative path for ``src``'
    severity = 'HIGH'
    tags = ['module']
    version_added = 'v4.0.0'

    def matchplay(self, file, play):
        if file['type'] == 'playbook':
            return []
        if 'template' in play:
            if not isinstance(play['template'], dict):
                return False
            if "../templates" in play['template']['src']:
                return [({'': play['template']},
                        self.shortdesc)]
        if 'win_template' in play:
            if not isinstance(play['win_template'], dict):
                return False
            if "../win_templates" in play['win_template']['src']:
                return ({'win_template': play['win_template']},
                        self.shortdesc)
        if 'copy' in play:
            if not isinstance(play['copy'], dict):
                return False
            if 'src' in play['copy']:
                if "../files" in play['copy']['src']:
                    return ({'sudo': play['copy']},
                            self.shortdesc)
        if 'win_copy' in play:
            if not isinstance(play['win_copy'], dict):
                return False
            if "../files" in play['win_copy']['src']:
                return ({'sudo': play['win_copy']},
                        self.shortdesc)
        return []
