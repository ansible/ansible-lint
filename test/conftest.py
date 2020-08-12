import os

import pytest

from ansiblelint.rules import RulesCollection

from . import RunFromText


@pytest.fixture
def default_rules_collection():
    return RulesCollection(rulesdirs=[os.path.abspath(os.path.join('lib',
                                                                   'ansiblelint',
                                                                   'rules'))])


@pytest.fixture
def default_text_runner(default_rules_collection):
    return RunFromText(default_rules_collection)


@pytest.fixture
def rule_runner(request):
    """Return runner for a specific rule class."""
    rule_class = request.param
    collection = RulesCollection()
    collection.register(rule_class())
    return RunFromText(collection)


# vim: et:sw=4:syntax=python:ts=4:
