"""Assure samples produced desire outcomes."""

import pytest

from ansiblelint.app import get_app
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.testing import run_ansible_lint


def test_example(default_rules_collection: RulesCollection) -> None:
    """example.yml is expected to have exact number of errors inside."""
    result = Runner(
        "examples/playbooks/example.yml",
        rules=default_rules_collection,
    ).run()
    assert len(result) == 22


@pytest.mark.parametrize(
    ("filename", "expected_results"),
    (
        pytest.param(
            "examples/playbooks/syntax-error-string.yml",
            [("syntax-check[unknown-module]", 6, 7)],
            id="0",
        ),
        pytest.param(
            "examples/playbooks/syntax-error.yml",
            [("syntax-check[specific]", 2, 3)],
            id="1",
        ),
    ),
)
def test_example_syntax_error(
    default_rules_collection: RulesCollection,
    filename: str,
    expected_results: list[tuple[str, int | None, int | None]],
) -> None:
    """Validates that loading valid YAML string produce error."""
    result = Runner(filename, rules=default_rules_collection).run()
    assert len(result) == len(expected_results)
    for i, expected in enumerate(expected_results):
        if expected[0] is not None:
            assert result[i].tag == expected[0]
        # This also ensures that line and column numbers start at 1, so they
        # match what editors will show (or output from other linters)
        if expected[1] is not None:
            assert result[i].lineno == expected[1]
        if expected[2] is not None:
            assert result[i].column == expected[2]


def test_example_custom_module(default_rules_collection: RulesCollection) -> None:
    """custom_module.yml is expected to pass."""
    app = get_app(offline=True)
    result = Runner(
        "examples/playbooks/custom_module.yml",
        rules=default_rules_collection,
    ).run()
    assert len(result) == 0, f"{app.runtime.cache_dir}"


def test_vault_full(default_rules_collection: RulesCollection) -> None:
    """Check ability to process fully vaulted files."""
    result = Runner(
        "examples/playbooks/vars/vault_full.yml",
        rules=default_rules_collection,
    ).run()
    assert len(result) == 0


def test_vault_partial(
    default_rules_collection: RulesCollection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Check ability to process files that container !vault inside."""
    result = Runner(
        "examples/playbooks/vars/vault_partial.yml",
        rules=default_rules_collection,
    ).run()
    assert len(result) == 0
    # Ensure that we do not have side-effect extra logging even if the vault
    # content cannot be decrypted.
    assert caplog.record_tuples == []


def test_custom_kinds() -> None:
    """Check if user defined kinds are used."""
    result = run_ansible_lint("-vv", "--offline", "examples/other/")
    assert result.returncode == 0
    # .yaml-too is not a recognized extension and unless is manually defined
    # in our ansible-lint config, the test would not identify it as yaml file.
    assert "Examining examples/other/some.yaml-too of type yaml" in result.stderr
    assert "Examining examples/other/some.j2.yaml of type jinja2" in result.stderr


def test_bug_3216(capsys: pytest.CaptureFixture[str]) -> None:
    """Check that we hide ansible-core originating warning about fallback on unique filter."""
    result = run_ansible_lint(
        "-vv",
        "--offline",
        "examples/playbooks/bug-core-warning-unique-filter-fallback.yml",
    )
    captured = capsys.readouterr()
    assert result.returncode == 0
    warn_msg = "Falling back to Ansible unique filter"
    assert warn_msg not in captured.err
    assert warn_msg not in captured.out
