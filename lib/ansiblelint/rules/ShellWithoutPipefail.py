import re

from ansiblelint.rules import AnsibleLintRule


class ShellWithoutPipefail(AnsibleLintRule):
    id = '306'
    shortdesc = 'Shells that use pipes should set the pipefail option'
    description = (
        'Without the pipefail option set, a shell command that '
        'implements a pipeline can fail and still return 0. If '
        'any part of the pipeline other than the terminal command '
        'fails, the whole pipeline will still return 0, which may '
        'be considered a success by Ansible. '
        'Pipefail is available in the bash shell.'
    )
    severity = 'MEDIUM'
    tags = ['command-shell']
    version_added = 'v4.1.0'

    _pipefail_re = re.compile(r"^\s*set.*[+-][A-z]*o\s*pipefail")
    _pipe_re = re.compile(r"(?<!\|)\|(?!\|)")

    def matchtask(self, file, task):
        if task["__ansible_action_type__"] != "task":
            return False

        if task["action"]["__ansible_module__"] != "shell":
            return False

        if task.get("ignore_errors"):
            return False

        unjinjad_cmd = self.unjinja(
            ' '.join(task["action"].get("__ansible_arguments__", [])))

        return (self._pipe_re.search(unjinjad_cmd) and
                not self._pipefail_re.match(unjinjad_cmd))
