import unittest

from ansiblelint import RulesCollection, default_rulesdir


class TestAlwaysRun(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.extend(
            RulesCollection.create_from_directory(default_rulesdir)
        )

    def test_serverity_valid(self):
        valid_severity_values = [
            'VERY_HIGH',
            'HIGH',
            'MEDIUM',
            'LOW',
            'VERY_LOW',
            'INFO',
        ]
        for rule in self.collection:
            self.assertIn(rule.severity, valid_severity_values)
