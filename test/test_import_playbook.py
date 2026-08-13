"""Test ability to import playbooks."""

from pathlib import Path

from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.testing import run_ansible_lint


def test_task_hook_import_playbook(default_rules_collection: RulesCollection) -> None:
    """Assures import_playbook includes are recognized."""
    playbook_path = "examples/playbooks/playbook-parent.yml"
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    results_text = str(results)
    assert len(runner.lintables) == 2
    assert len(results) == 2
    # Assures we detected the issues from imported playbook
    assert "Commands should not change things" in results_text
    assert "[name]" in results_text
    assert "All tasks should be named" in results_text


def test_import_playbook_from_collection(
    default_rules_collection: RulesCollection,
) -> None:
    """Assures import_playbook from collection."""
    playbook_path = "examples/playbooks/test_import_playbook.yml"
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    assert len(runner.lintables) == 1
    assert len(results) == 0


def test_import_playbook_invalid(
    default_rules_collection: RulesCollection,
) -> None:
    """Assures import_playbook from collection."""
    playbook_path = "examples/playbooks/test_import_playbook_invalid.yml"
    runner = Runner(playbook_path, rules=default_rules_collection)
    results = runner.run()

    assert len(runner.lintables) == 1
    assert len(results) == 1
    assert results[0].tag == "syntax-check[specific]"
    # ansible-core devel changes line number reported to 4 (better)
    assert results[0].lineno in (2, 4)


def test_import_playbook_extra_vars(tmp_path: Path) -> None:
    """Assure extra_vars reach a playbook imported via import_playbook (#5042)."""
    (tmp_path / ".ansible-lint").write_text("extra_vars:\n  my_host: localhost\n")
    (tmp_path / "inner.yml").write_text(
        '---\n- name: Inner play\n  hosts: "{{ my_host }}"\n  gather_facts: false\n'
        "  tasks:\n    - name: Noop\n      ansible.builtin.debug:\n        msg: hi\n",
    )
    (tmp_path / "outer.yml").write_text(
        "---\n- name: Import inner\n  ansible.builtin.import_playbook: inner.yml\n",
    )

    result = run_ansible_lint("outer.yml", cwd=tmp_path)

    # Without extra_vars propagation, inner.yml fails its syntax check and is
    # silently dropped, leaving only one file processed while the run exits 0.
    assert result.returncode == 0, result.stderr
    assert "2 files processed" in result.stderr
    assert "Failed to load" not in result.stderr
