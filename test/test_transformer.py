import os
from argparse import Namespace
from typing import Any, List, Set, Type

import pytest

from ansiblelint.cli import abspath
from ansiblelint.rules import RulesCollection

# noinspection PyProtectedMember
from ansiblelint.runner import _get_matches, LintResult
from ansiblelint.transformer import Transformer
from ansiblelint.transforms import TransformsCollection

LOTS_OF_WARNINGS_PLAYBOOK = abspath(
    'examples/playbooks/lots_of_warnings.yml', os.getcwd()
)


@pytest.fixture
def runner_result(
    config_options: Namespace,
    default_rules_collection: RulesCollection,
    playbook: str,
    exclude: List[str],
) -> LintResult:
    config_options.lintables = [playbook]
    config_options.exclude_paths = exclude
    result = _get_matches(rules=default_rules_collection, options=config_options)
    return result


@pytest.mark.parametrize(
    ('playbook', 'exclude', 'matches_count', 'fixed_count'),
    (
        pytest.param(
            'examples/playbooks/nomatchestest.yml', [], 0, 0, id="nomatchestest"
        ),
        pytest.param('examples/playbooks/unicode.yml', [], 1, 0, id="unicode"),
        pytest.param(
            LOTS_OF_WARNINGS_PLAYBOOK,
            [LOTS_OF_WARNINGS_PLAYBOOK],
            0,
            0,
            id="lots_of_warnings",
        ),
        pytest.param('examples/playbooks/become.yml', [], 0, 0, id="become"),
        pytest.param(
            'examples/playbooks/contains_secrets.yml', [], 0, 0, id="contains_secrets"
        ),
    ),
)
def test_transformer(
    default_transforms_collection: TransformsCollection,
    runner_result: LintResult,
    matches_count: int,
    fixed_count: int,
) -> None:
    """
    Test that transformer can go through any corner cases.

    Based on TestRunner::test_runner
    """

    transformer = Transformer(
        result=runner_result, transforms=default_transforms_collection
    )
    transformer.run()

    matches = runner_result.matches
    assert len(matches) == matches_count

    fixed = [match for match in matches if match.fixed]
    assert len(fixed) == fixed_count
