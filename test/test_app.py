"""Test for app module."""

from pathlib import Path

from ansiblelint.constants import RC
from ansiblelint.file_utils import Lintable
from ansiblelint.testing import run_ansible_lint


def test_generate_ignore(tmp_path: Path) -> None:
    """Validate that --generate-ignore dumps expected ignore to the file."""
    lintable = Lintable(tmp_path / "vars.yaml")
    lintable.content = "foo: 1\nbar:   baz\n"
    lintable.write(force=True)
    ignore_file = tmp_path / ".ansible-lint-ignore"
    assert not ignore_file.exists()
    result = run_ansible_lint(lintable.filename, "--generate-ignore", cwd=tmp_path)
    assert result.returncode == 2

    assert ignore_file.exists()
    with ignore_file.open(encoding="utf-8") as f:
        assert "vars.yaml yaml[colons]\n" in f.readlines()
    # Run again and now we expect to succeed as we have an ignore file.
    result = run_ansible_lint(lintable.filename, cwd=tmp_path)
    assert result.returncode == 0


def test_app_no_matches(tmp_path: Path) -> None:
    """Validate that linter returns special exit code if no files are analyzed."""
    result = run_ansible_lint(cwd=tmp_path)
    assert result.returncode == RC.NO_FILES_MATCHED


def test_with_inventory_concurrent_syntax_checks(tmp_path: Path) -> None:
    """Validate using inventory file with concurrent syntax checks aren't faulty."""
    (tmp_path / "ansible.cfg").write_text("[defaults]\ninventory = foo\n")
    (tmp_path / "foo").write_text("[group_name]\nhost1\nhost2\n")
    lintable1 = Lintable(tmp_path / "playbook1.yml")
    lintable2 = Lintable(tmp_path / "playbook2.yml")
    lintable1.content = "---\n- name: Test\n  hosts:\n    - group_name\n  serial: \"{{ batch | default(groups['group_name'] | length) }}\"\n"
    lintable2.content = "---\n- name: Test\n  hosts:\n    - group_name\n  serial: \"{{ batch | default(groups['group_name'] | length) }}\"\n"
    lintable1.kind = "playbook"
    lintable2.kind = "playbook"
    lintable1.write(force=True)
    lintable2.write(force=True)

    counter = 0
    while counter < 3:
        result = run_ansible_lint(lintable1.filename, lintable2.filename, cwd=tmp_path)
        assert result.returncode == RC.SUCCESS
        # AttributeError err is expected to look like what's reported here,
        # https://github.com/ansible/ansible-lint/issues/4446.
        assert "AttributeError" not in result.stderr
        counter += 1
