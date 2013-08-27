import unittest

import ansiblelint.utils as utils


class TestUtils(unittest.TestCase):

    def test_tokenize_blank(self):
        r = utils.tokenize("")
        self.assertEquals(r, list(['']))

    def test_tokenize_single_word(self):
        r = utils.tokenize("vars:")
        self.assertEquals(r, ["vars"])

    def test_tokenize_string_module_and_arg(self):
        r = utils.tokenize("hello: a=1")
        self.assertEquals(r[0], "hello")
        self.assertEquals(r[1], {"a": "1"})

    def test_tokenize_strips_action(self):
        r = utils.tokenize("action: hello a=1")
        self.assertEquals(r[0], "hello")
        self.assertEquals(r[1], {"a": "1"})
        
    def test_tokenize_more_than_one_arg(self):
        r = utils.tokenize("action: whatever bobbins x=y z=x c=3")
        self.assertEquals(r[0], "whatever")
        self.assertEquals(r[1], "bobbins")
        self.assertIn('x', r[2])
        self.assertIn('z', r[3])
        self.assertIn('c', r[4])
