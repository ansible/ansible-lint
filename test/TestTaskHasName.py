import unittest
from ansiblelint import Runner, RulesCollection
from ansiblelint.rules.TaskHasNameRule import TaskHasNameRule


class TestTaskHasNameRule(unittest.TestCase):
    collection = RulesCollection()

    def setUp(self):
        self.collection.register(TaskHasNameRule())

    def test_file_positive(self):
        success = 'test/task-has-name-success.yml'
        good_runner = Runner(self.collection, success, [], [], [])
        self.assertEqual([], good_runner.run())

    def test_file_negative(self):
        failure = 'test/task-has-name-failure.yml'
        bad_runner = Runner(self.collection, failure, [], [], [])
        errs = bad_runner.run()
        self.assertEqual(2, len(errs))
