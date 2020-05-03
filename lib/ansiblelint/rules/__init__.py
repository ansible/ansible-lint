"""All internal ansible-lint rules."""
import re
from ansiblelint.skip_utils import get_rule_skips_from_line
from ansiblelint.skip_utils import append_skipped_rules
from ansiblelint.errors import Match
import ansiblelint.utils


class AnsibleLintRule(object):

    def __repr__(self):
        """Return a AnsibleLintRule instance representation."""
        return self.id + ": " + self.shortdesc

    def verbose(self):
        return self.id + ": " + self.shortdesc + "\n  " + self.description

    match = None
    matchtask = None
    matchplay = None

    @staticmethod
    def unjinja(text):
        return re.sub(r"{{[^}]*}}", "JINJA_VAR", text)

    def matchlines(self, file, text):
        matches = []
        if not self.match:
            return matches
        # arrays are 0-based, line numbers are 1-based
        # so use prev_line_no as the counter
        for (prev_line_no, line) in enumerate(text.split("\n")):
            if line.lstrip().startswith('#'):
                continue

            rule_id_list = get_rule_skips_from_line(line)
            if self.id in rule_id_list:
                continue

            result = self.match(file, line)
            if not result:
                continue
            message = None
            if isinstance(result, str):
                message = result
            matches.append(Match(prev_line_no + 1, line,
                           file['path'], self, message))
        return matches

    def matchtasks(self, file, text):
        matches = []
        if not self.matchtask:
            return matches

        if file['type'] == 'meta':
            return matches

        yaml = ansiblelint.utils.parse_yaml_linenumbers(text, file['path'])
        if not yaml:
            return matches

        yaml = append_skipped_rules(yaml, text, file['type'])

        for task in ansiblelint.utils.get_normalized_tasks(yaml, file):
            if self.id in task.get('skipped_rules', ()):
                continue

            if 'action' not in task:
                continue
            result = self.matchtask(file, task)
            if not result:
                continue

            message = None
            if isinstance(result, str):
                message = result
            task_msg = "Task/Handler: " + ansiblelint.utils.task_to_str(task)
            matches.append(Match(task[ansiblelint.utils.LINE_NUMBER_KEY], task_msg,
                           file['path'], self, message))
        return matches

    def _unpack_result(self, play, result):
        linenumber = play[ansiblelint.utils.LINE_NUMBER_KEY]
        if len(result) == 2:
            section, message = result
        else:
            section, linenumber, message = result
        return section, linenumber, message

    def matchyaml(self, file, text):
        matches = []
        if not self.matchplay:
            return matches

        yaml = ansiblelint.utils.parse_yaml_linenumbers(text, file['path'])
        if not yaml:
            return matches

        if isinstance(yaml, dict):
            yaml = [yaml]

        yaml = ansiblelint.skip_utils.append_skipped_rules(yaml, text, file['type'])

        for play in yaml:
            if self.id in play.get('skipped_rules', ()):
                continue

            result = self.matchplay(file, play)
            if not result:
                continue

            if isinstance(result, tuple):
                result = [result]

            if not isinstance(result, list):
                raise TypeError("{} is not a list".format(result))

            for match in result:
                section, linenumber, message = self._unpack_result(play, match)
                matches.append(Match(linenumber,
                                     section, file['path'], self, message))
        return matches
