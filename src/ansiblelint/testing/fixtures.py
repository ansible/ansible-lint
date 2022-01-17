"""PyTest Fixtures.

They should not be imported, instead add code below to your root conftest.py
file:

pytest_plugins = ['ansiblelint.testing']
"""
import copy
import os
from argparse import Namespace
from pathlib import Path
from typing import Iterator, Union

import pytest
from _pytest.fixtures import SubRequest

from ansiblelint.config import options  # noqa: F401
from ansiblelint.constants import DEFAULT_RULESDIR
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.testing import RunFromText


@pytest.fixture
def play_file_path(tmp_path: Path) -> str:
    """Fixture to return a playbook path."""
    p = tmp_path / 'playbook.yml'
    return str(p)


@pytest.fixture
def runner(
    play_file_path: Union[Lintable, str], default_rules_collection: RulesCollection
) -> Runner:
    """Fixture to return a Runner() instance."""
    return Runner(play_file_path, rules=default_rules_collection)


@pytest.fixture
def default_rules_collection() -> RulesCollection:
    """Return default rule collection."""
    assert os.path.isdir(DEFAULT_RULESDIR)
    # For testing we want to manually enable opt-in rules
    options.enable_list = ['no-same-owner']
    return RulesCollection(rulesdirs=[DEFAULT_RULESDIR], options=options)


@pytest.fixture
def default_text_runner(default_rules_collection: RulesCollection) -> RunFromText:
    """Return RunFromText instance for the default set of collections."""
    return RunFromText(default_rules_collection)


@pytest.fixture
def rule_runner(request: SubRequest, config_options: Namespace) -> RunFromText:
    """Return runner for a specific rule class."""
    rule_class = request.param
    config_options.enable_list.append(rule_class().id)
    collection = RulesCollection(options=config_options)
    collection.register(rule_class())
    return RunFromText(collection)


@pytest.fixture
def config_options() -> Iterator[Namespace]:
    """Return configuration options that will be restored after testrun."""
    global options  # pylint: disable=global-statement
    original_options = copy.deepcopy(options)
    yield options
    options = original_options


@pytest.fixture
def _play_files(tmp_path: Path, request: SubRequest) -> None:
    if request.param is None:
        return
    for play_file in request.param:
        print(play_file.name)
        p = tmp_path / play_file.name
        os.makedirs(os.path.dirname(p), exist_ok=True)
        p.write_text(play_file.content)
