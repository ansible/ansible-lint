"""PyTest Fixtures.

They should not be imported, instead add code below to your root conftest.py
file:

pytest_plugins = ['ansiblelint.testing']
"""
import os

import pytest

from ansiblelint.constants import DEFAULT_RULESDIR
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.testing import RunFromText


@pytest.fixture
def play_file_path(tmp_path):
    """Fixture to return a playbook path."""
    p = tmp_path / 'playbook.yml'
    return str(p)


@pytest.fixture
def runner(play_file_path, default_rules_collection):
    """Fixture to return a Runner() instance."""
    return Runner(
        rules=default_rules_collection,
        lintable=play_file_path)


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


@pytest.fixture
def _play_files(tmp_path, request):
    if request.param is None:
        return
    for play_file in request.param:
        print(play_file.name)
        p = tmp_path / play_file.name
        os.makedirs(os.path.dirname(p), exist_ok=True)
        p.write_text(play_file.content)
