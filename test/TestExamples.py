"""Assure samples produced desire outcomes."""
import os

import pytest

from ansiblelint.runner import Runner
from ansiblelint.testing import run_ansible_lint


@pytest.fixture
def _change_into_examples_dir(request):
    os.chdir('examples')
    yield
    os.chdir('..')


@pytest.mark.usefixtures('_change_into_examples_dir')
def test_example(default_rules_collection):
    """example.yml is expected to have 16 match errors inside."""
    result = Runner('playbooks/example.yml', rules=default_rules_collection).run()
    assert len(result) == 16


@pytest.mark.parametrize(
    "filename",
    (
        pytest.param(
            'examples/playbooks/syntax-error-string.yml', id='syntax-error-string'
        ),
        pytest.param('examples/playbooks/syntax-error.yml', id='syntax-error'),
    ),
)
def test_example_syntax_error(default_rules_collection, filename):
    """Validates that loading valid YAML string produce error."""
    result = Runner(filename, rules=default_rules_collection).run()
    assert len(result) >= 1
    passed = False
    for match in result:
        if match.rule.id == "syntax-check":
            passed = True
    assert passed, result


def test_example_custom_module(default_rules_collection):
    """custom_module.yml is expected to pass."""
    result = Runner(
        'examples/playbooks/custom_module.yml', rules=default_rules_collection
    ).run()
    assert len(result) == 0


def test_full_vault(default_rules_collection):
    """custom_module.yml is expected to pass."""
    result = Runner(
        'examples/playbooks/vars/not_decryptable.yml', rules=default_rules_collection
    ).run()
    assert len(result) == 0


def test_custom_kinds():
    """Check if user defined kinds are used."""
    result = run_ansible_lint('-vv', '--offline', 'examples/other/')
    assert result.returncode == 0
    # .yaml-too is not a recognized extension and unless is manually defined
    # in our .ansible-lint config, the test would not identify it as yaml file.
    assert "Examining examples/other/some.yaml-too of type yaml" in result.stderr
