import os

import pytest
from test import RunFromText

from ansiblelint.rules import RulesCollection


@pytest.fixture
def default_rules_collection():
    return RulesCollection(rulesdirs=[os.path.abspath(os.path.join('lib',
                                                                   'ansiblelint',
                                                                   'rules'))])


@pytest.fixture
def default_text_runner(default_rules_collection):
    return RunFromText(default_rules_collection)


# vim: et:sw=4:syntax=python:ts=4:
