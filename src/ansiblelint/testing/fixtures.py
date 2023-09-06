"""PyTest Fixtures.

They should not be imported, instead add code below to your root conftest.py
file:

pytest_plugins = ['ansiblelint.testing']
"""
from __future__ import annotations

import copy
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ansiblelint.config import Options, options
from ansiblelint.constants import DEFAULT_RULESDIR
from ansiblelint.rules import RulesCollection
from ansiblelint.testing import RunFromText

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Iterator

    from _pytest.fixtures import SubRequest


# The sessions scope does not apply to xdist, so we will still have one
# session for each worker, but at least it will a limited number.
@pytest.fixture(name="default_rules_collection", scope="session")
def fixture_default_rules_collection() -> RulesCollection:
    """Return default rule collection."""
    assert DEFAULT_RULESDIR.is_dir()
    # For testing we want to manually enable opt-in rules
    test_options = copy.deepcopy(options)
    test_options.enable_list = ["no-same-owner"]
    # That is instantiated very often and do want to avoid ansible-galaxy
    # install errors due to concurrency.
    test_options.offline = True
    return RulesCollection(rulesdirs=[DEFAULT_RULESDIR], options=test_options)


@pytest.fixture()
def default_text_runner(default_rules_collection: RulesCollection) -> RunFromText:
    """Return RunFromText instance for the default set of collections."""
    return RunFromText(default_rules_collection)


@pytest.fixture()
def rule_runner(request: SubRequest, config_options: Options) -> RunFromText:
    """Return runner for a specific rule class."""
    rule_class = request.param
    config_options.enable_list.append(rule_class().id)
    collection = RulesCollection(options=config_options)
    collection.register(rule_class())
    return RunFromText(collection)


@pytest.fixture(name="config_options")
def fixture_config_options() -> Iterator[Options]:
    """Return configuration options that will be restored after testrun."""
    global options  # pylint: disable=global-statement,invalid-name # noqa: PLW0603
    original_options = copy.deepcopy(options)
    yield options
    options = original_options


@pytest.fixture(name="copy_examples_dir")
def fixture_copy_examples_dir(
    tmp_path: Path,
    config_options: Namespace,
) -> Iterator[tuple[Path, Path]]:
    """Fixture that copies the examples/ dir into a tmpdir."""
    examples_dir = Path("examples")

    shutil.copytree(examples_dir, tmp_path / "examples")
    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        config_options.cwd = tmp_path
        yield old_cwd, tmp_path
    finally:
        os.chdir(old_cwd)
