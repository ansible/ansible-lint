import unittest

import ansiblelint.utils
from ansiblelint import AnsibleLintRule

class EMatcherRule(AnsibleLintRule):
    ID = 'TEST0001'
    DESCRIPTION = 'This is a test rule that looks for lines ' + \
                  'containing the letter e'
    TAGS = ['fake', 'dummy']

    def __init__(self):
        super(EMatcherRule, self).__init__(id=EMatcherRule.ID, 
                                           description=EMatcherRule.DESCRIPTION,
                                           tags=EMatcherRule.TAGS)

    def prematch(self,playbook):
        return ansiblelint.utils.matchlines(playbook, lambda x : "e" in x)


class TestRule(unittest.TestCase):

    def test_rule_matching(self):
        text = ""
        with open('test/ematchtest.txt') as f:
            text = f.read()
        ematcher = EMatcherRule()
        linenos = ematcher.prematch(text)
        self.assertEqual(linenos, [1,3,5])

