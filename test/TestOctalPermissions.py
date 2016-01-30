import unittest
import ansiblelint.utils
from itertools import permutations, combinations
from ansiblelint import RulesCollection
from ansiblelint.rules.OctalPermissionsRule import OctalPermissionsRule

class TestOctalPermissionsRule(unittest.TestCase):
    rule = OctalPermissionsRule()
    one_to_seven = [ str(digit) for digit in range(8) ]
    # Problematic modes are any permutation of three digits in 1-7
    bad_permutations = set(permutations(combinations(one_to_seven, 3), 3))
    # Join tuples to strings and flatten the list
    bad_modes = [
            "".join(tup) for lst in bad_permutations for tup in lst
    ]
    # Valid modes are just the bad ones with a leading zero
    good_modes = [ "0" + mode for mode in bad_modes ]

    # Ensure that the given regex matches all octal numbers appropriately
    def test_regex_positives(self):
        for good in self.good_modes:
            self.assertRegexpMatches(good, self.rule.valid_permissions_regex)

    def test_regex_negatives(self):
        for bad in self.bad_modes:
            self.assertNotRegexpMatches(bad, self.rule.valid_permissions_regex)

    def test_positives(self):
        # Construct valid task dictionaries for every possible mode
        successes = [{ "action": { "mode" : mode } for mode in self.good_modes }]
        # Loop through all of them and ensure the rule is working
        for success in successes:
            self.assertFalse(self.rule.matchtask("", success))

    def test_failures(self):
        failures = [{ "action": { "mode" : mode } for mode in self.bad_modes }]
        for failure in failures:
            self.assertTrue(self.rule.matchtask("", failure))

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
        self.assertEqual(3, len(bad_runner.run()))
