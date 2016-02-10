import unittest

from ansiblelint.rules.SudoRule import SudoRule
import ansiblelint.utils


class TestSudoRule(unittest.TestCase):
    simple_dict_yaml = {
        'value1': '{foo}}',
        'value2': 2,
        'value3': ['foo', 'bar', '{baz}}'],
        'value4': '{bar}',
        'value5': '{{baz}',
    }

    def setUp(self):
        self.rule = SudoRule()

    def test_check_value_simple_matching(self):
        result = self.rule._check_value("sudo: yes")
        self.assertEquals(0, len(result))

    def test_check_value_shallow_dict(self):
        result = self.rule._check_value({ 'sudo': 'yes', 'sudo_user': 'somebody' })
        self.assertEquals(2, len(result))

    def test_check_value_nested(self):
        yaml = [
            {
                'hosts': 'all',
                'sudo': 'yes',
                'sudo_user': 'nobody',
                'tasks': [
                   {
                      'name': 'test',
                      'debug': 'msg=test',
                      'sudo': 'yes',
                      'sudo_user': 'somebody'
                   }
                ]
            }
        ]
        result = self.rule._check_value(yaml)
        self.assertEquals(2, len(result))


class TestSudoRuleWithFile(unittest.TestCase):
    file1 = 'test/sudo.yml'

    def setUp(self):
        self.rule = SudoRule()

    def test_matchplay_sudo(self):
        yaml = ansiblelint.utils.parse_yaml_linenumbers(open(self.file1).read())

        self.assertTrue(yaml)
        for play in yaml:
            result = self.rule.matchplay(self.file1, play)
            self.assertEquals(2, len(result))
