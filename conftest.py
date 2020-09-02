"""PyTest Fixtures."""
import os

import pytest

from ansiblelint.constants import DEFAULT_RULESDIR
from ansiblelint.rules import RulesCollection
from ansiblelint.testing import RunFromText


@pytest.fixture
def default_rules_collection():
    """Return default rule collection."""
    assert os.path.isdir(DEFAULT_RULESDIR)
    return RulesCollection(rulesdirs=[DEFAULT_RULESDIR])


@pytest.fixture
def default_text_runner(default_rules_collection):
    """Return RunFromText instance for the default set of collections."""
    return RunFromText(default_rules_collection)


@pytest.fixture
def rule_runner(request):
    """Return runner for a specific rule class."""
    rule_class = request.param
    collection = RulesCollection()
    collection.register(rule_class())
    return RunFromText(collection)
