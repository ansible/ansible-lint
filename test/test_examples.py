"""Assure samples produced desire outcomes."""
import pytest

from ansiblelint.app import get_app
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.testing import run_ansible_lint


def test_example(default_rules_collection: RulesCollection) -> None:
    """example.yml is expected to have exact number of errors inside."""
    result = Runner(
        "examples/playbooks/example.yml", rules=default_rules_collection
    ).run()
    assert len(result) == 19


@pytest.mark.parametrize(
    ("filename", "line", "column"),
    (
        pytest.param(
            "examples/playbooks/syntax-error-string.yml", 6, 7, id="syntax-error"
        ),
        pytest.param("examples/playbooks/syntax-error.yml", 2, 3, id="syntax-error"),
    ),
)
def test_example_syntax_error(
    default_rules_collection: RulesCollection, filename: str, line: int, column: int
) -> None:
    """Validates that loading valid YAML string produce error."""
    result = Runner(filename, rules=default_rules_collection).run()
    assert len(result) == 1
    assert result[0].rule.id == "syntax-check"
    # This also ensures that line and column numbers start at 1, so they
    # match what editors will show (or output from other linters)
    assert result[0].linenumber == line
    assert result[0].column == column


def test_example_custom_module(default_rules_collection: RulesCollection) -> None:
    """custom_module.yml is expected to pass."""
    app = get_app()
    result = Runner(
        "examples/playbooks/custom_module.yml", rules=default_rules_collection
    ).run()
    assert len(result) == 0, f"{app.runtime.cache_dir}"


def test_full_vault(default_rules_collection: RulesCollection) -> None:
    """custom_module.yml is expected to pass."""
    result = Runner(
        "examples/playbooks/vars/not_decryptable.yml", rules=default_rules_collection
    ).run()
    assert len(result) == 0


def test_custom_kinds() -> None:
    """Check if user defined kinds are used."""
    result = run_ansible_lint("-vv", "--offline", "examples/other/")
    assert result.returncode == 0
    # .yaml-too is not a recognized extension and unless is manually defined
    # in our ansible-lint config, the test would not identify it as yaml file.
    assert "Examining examples/other/some.yaml-too of type yaml" in result.stderr
    assert "Examining examples/other/some.j2.yaml of type jinja2" in result.stderr
