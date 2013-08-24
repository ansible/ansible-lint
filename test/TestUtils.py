import unittest

import ansiblelint.utils as utils


class TestUtils(unittest.TestCase):

    def test_tokenize_blank(self):
        (m, a) = utils.tokenize("")
        self.assertEquals(m, "")
        self.assertEquals(a, dict())

    def test_tokenize_single_word(self):
        (m, a) = utils.tokenize("vars:")
        self.assertEquals(m, "vars")
        self.assertEquals(a, dict())

    def test_tokenize_string_module_and_arg(self):
        (m, a) = utils.tokenize("hello: a=1")
        self.assertEquals(m, "hello")
        self.assertEquals(a, {"a": "1"})

    def test_tokenize_strips_action(self):
        (m, a) = utils.tokenize("action: hello a=1")
        self.assertEquals(m, "hello")
        self.assertEquals(a, {"a": "1"})
        
    def test_tokenize_more_than_one_arg(self):
        (m, a) = utils.tokenize("action: whatever x=y z=x c=3")
        self.assertEquals(m, "whatever")
        self.assertEquals(len(a), 3)
        self.assertIn('x', a)
        self.assertIn('z', a)
        self.assertIn('c', a)
