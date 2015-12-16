import unittest

from ansiblelint.rules.MismatchedBracketRule import MismatchedBracketRule
import ansiblelint.utils


class TestMismatchedBracketRule(unittest.TestCase):
    simple_dict_yaml = {
        'value1': '{foo}}',
        'value2': 2,
        'value3': ['foo', 'bar', '{baz}}'],
        'value4': '{bar}',
        'value5': '{{baz}',
    }

    def setUp(self):
        self.rule = MismatchedBracketRule()

    def test_check_value_simple_matching(self):
        result = self.rule._check_value("{{foo}}")
        self.assertEquals(0, len(result))

    def test_check_value_simple_not_matching(self):
        result = self.rule._check_value("{{foo}")
        self.assertEquals(1, len(result))

    def test_check_value_shallow_dict(self):
        result = self.rule._check_value(self.simple_dict_yaml)
        self.assertEquals(3, len(result))

    def test_check_value_nested(self):
        yaml = [
            self.simple_dict_yaml,
            {
                'values': self.simple_dict_yaml,
                'more_values': [self.simple_dict_yaml, self.simple_dict_yaml],
            },
        ]

        result = self.rule._check_value(yaml)
        self.assertEquals(12, len(result))


class TestMismatchedBracketRuleWithFile(unittest.TestCase):
    file1 = 'test/bracketsmatchtest.yml'
    file2 = 'test/multiline-bracketsmatchtest.yml'
    file3 = 'test/multiline-brackets-do-not-match-test.yml'

    def setUp(self):
        self.yaml2 = ansiblelint.utils.parse_yaml_linenumbers(open(self.file2).read())

        self.rule = MismatchedBracketRule()

    def test_matchplay_file1(self):
        yaml = ansiblelint.utils.parse_yaml_linenumbers(open(self.file1).read())

        self.assertTrue(yaml)
        for play in yaml:
            result = self.rule.matchplay(self.file1, play)
            self.assertEquals(0, len(result))

    def test_matchplay_file2(self):
        yaml = ansiblelint.utils.parse_yaml_linenumbers(open(self.file2).read())

        self.assertTrue(yaml)
        for play in yaml:
            result = self.rule.matchplay(self.file2, play)
            self.assertEquals(0, len(result))

    def test_matchplay_file3(self):
        yaml = ansiblelint.utils.parse_yaml_linenumbers(open(self.file3).read())

        self.assertEquals(2, len(yaml))

        result = self.rule.matchplay(self.file3, yaml[0])
        self.assertEquals(1, len(result))

        result = self.rule.matchplay(self.file3, yaml[1])
        self.assertEquals(1, len(result))
