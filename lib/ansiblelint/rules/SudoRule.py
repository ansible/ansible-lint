from ansiblelint.rules import AnsibleLintRule


class SudoRule(AnsibleLintRule):
    id = '103'
    shortdesc = 'Deprecated sudo'
    description = 'Instead of ``sudo``/``sudo_user``, use ``become``/``become_user``.'
    severity = 'VERY_HIGH'
    tags = ['deprecated', 'ANSIBLE0008']
    version_added = 'historic'

    def _check_value(self, play_frag):
        results = []

        if isinstance(play_frag, dict):
            if 'sudo' in play_frag:
                results.append(({'sudo': play_frag['sudo']},
                                'Deprecated sudo feature', play_frag['__line__']))
            if 'sudo_user' in play_frag:
                results.append(({'sudo_user': play_frag['sudo_user']},
                                'Deprecated sudo_user feature', play_frag['__line__']))
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

    def matchplay(self, file, play):
        return self._check_value(play)
