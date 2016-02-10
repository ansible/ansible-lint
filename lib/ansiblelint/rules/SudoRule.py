from ansiblelint import AnsibleLintRule


class SudoRule(AnsibleLintRule):
    id = 'ANSIBLE0008'
    shortdesc = 'Deprecated sudo'
    description = 'Instead of sudo/sudo_user, use become/become_user.'
    tags = ['deprecated']

    def _check_value(self, play_frag):
        results = []

        if isinstance(play_frag, dict):
            if 'sudo' in play_frag:
                results.append(({'sudo': play_frag['sudo']},
                                'deprecated sudo feature'))
            if 'sudo_user' in play_frag:
                results.append(({'sudo_user': play_frag['sudo_user']},
                                'deprecated sudo_user feature'))

        if isinstance(play_frag, list):
            for item in play_frag:
                output = self._check_value(item)
                if output:
                    results += output

        return results

    def matchplay(self, file, play):
        return self._check_value(play)
