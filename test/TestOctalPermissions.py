import unittest
import ansiblelint.utils
from itertools import permutations, combinations
from ansiblelint import RulesCollection
from ansiblelint.rules.OctalPermissionsRule import OctalPermissionsRule

class TestOctalPermissionsRule(unittest.TestCase):
    rule = OctalPermissionsRule()
    one_to_seven = [ str(digit) for digit in range(8) ]
    # All possible modes are any permutation of three digits in 1-7
    bad_permutations = set(permutations(combinations(one_to_seven, 3), 3))
    # Join tuples to strings and flatten the list
    modes = [ "".join(tup) for lst in bad_permutations for tup in lst ]
    bad_modes = [ "    mode: " + mode for mode in modes ]
    # Valid modes are just the bad ones with a leading zero
    good_modes = [ "    mode: 0" + mode for mode in modes ]

    # Ensure that the given regex matches all octal numbers appropriately
    def test_regex_positives(self):
        for good in self.good_modes:
            self.assertRegexpMatches(good, self.rule.mode_regex)
            self.assertRegexpMatches(good, self.rule.valid_mode_regex)

    def test_regex_negatives(self):
        for bad in self.bad_modes:
            self.assertRegexpMatches(bad, self.rule.mode_regex)
            self.assertNotRegexpMatches(bad, self.rule.valid_mode_regex)

class TestOctalPermissionsRuleWithFile(unittest.TestCase):
    collection = RulesCollection()

    def test_file_positive(self):
        self.collection.register(OctalPermissionsRule())
        success = 'test/octalpermissions-success.yml'
        good_runner = ansiblelint.Runner(self.collection, [success], [], [], [])
        self.assertEqual([], good_runner.run())

    def test_files(self):
        self.collection.register(OctalPermissionsRule())
        failure = 'test/octalpermissions-failure.yml'
        bad_runner = ansiblelint.Runner(self.collection, [failure], [], [], [])
        errs = bad_runner.run()
        # TODO: all errors are counted twice. Why?
        self.assertEqual(6, len(errs))
