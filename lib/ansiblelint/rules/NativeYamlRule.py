from ansiblelint import AnsibleLintRule
import re

class NativeYamlRule(AnsibleLintRule):
    id = '509'
    shortdesc = ("Tasks should use native YAML syntax")
    description = ("Instead of using the key=value shorthand, use native YAML syntax.")
    tags = ['task']

    bracket_regex = re.compile('(\s[^ ]*=([^\{\" ]*(\{\{\s[^ ]*\s\}\})?))+$')

    def match(self, file, line):
        return self.bracket_regex.search(line)
