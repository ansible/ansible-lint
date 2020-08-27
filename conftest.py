"""PyTest Fixtures."""
import os
from test import RunFromText

import pytest

import ansiblelint.rules as rules


def pytest_configure(config):
    """Add rule folder to test include for running embedded rule tests."""
    config.args.append(os.path.dirname(rules.__file__))


@pytest.fixture
def default_rules_collection():
    """Return default rules collection."""
    return rules.RulesCollection(rulesdirs=[os.path.abspath(os.path.join('lib',
                                                                         'ansiblelint',
                                                                         'rules'))])


@pytest.fixture
def default_text_runner(default_rules_collection):
    """Return TextRunner instance."""
    return RunFromText(default_rules_collection)


@pytest.fixture
def rule_runner(request):
    """Return runner for a specific rule class."""
    rule_class = request.param
    collection = rules.RulesCollection()
    collection.register(rule_class())
    return RunFromText(collection)


# vim: et:sw=4:syntax=python:ts=4:
