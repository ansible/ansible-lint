"""Test for app module."""

from pathlib import Path

import pytest

from ansiblelint.constants import RC
from ansiblelint.file_utils import Lintable
from ansiblelint.testing import run_ansible_lint


def test_generate_ignore(tmp_path: Path) -> None:
    """Validate that --generate-ignore dumps expected ignore to the file."""
    lintable = Lintable(tmp_path / "vars.yaml")
    lintable.content = "foo: bar\nfoo: baz\n"
    lintable.write(force=True)
    ignore_file = tmp_path / ".ansible-lint-ignore"
    assert not ignore_file.exists()
    result = run_ansible_lint(lintable.filename, "--generate-ignore", cwd=tmp_path)
    assert result.returncode == 2

    assert ignore_file.exists()
    with ignore_file.open(encoding="utf-8") as f:
        assert "vars.yaml yaml[key-duplicates]\n" in f.readlines()
    # Run again and now we expect to succeed as we have an ignore file.
    result = run_ansible_lint(lintable.filename, cwd=tmp_path)
    assert result.returncode == 0


def test_app_no_matches(tmp_path: Path) -> None:
    """Validate that linter returns special exit code if no files are analyzed."""
    result = run_ansible_lint(cwd=tmp_path)
    assert result.returncode == RC.NO_FILES_MATCHED


@pytest.mark.parametrize(
    "inventory_opts",
    (
        pytest.param(["-I", "inventories/foo"], id="1"),
        pytest.param(
            [
                "-I",
                "inventories/bar",
                "-I",
                "inventories/baz",
            ],
            id="2",
        ),
        pytest.param(
            [
                "-I",
                "inventories/foo,inventories/bar",
                "-I",
                "inventories/baz",
            ],
            id="3",
        ),
    ),
)
def test_with_inventory(inventory_opts: list[str]) -> None:
    """Validate using --inventory remedies syntax-check[specific] violation."""
    lintable = Lintable("examples/playbooks/test_using_inventory.yml")
    result = run_ansible_lint(lintable.filename, *inventory_opts)
    assert result.returncode == RC.SUCCESS


@pytest.mark.parametrize(
    ("inventory_opts", "error_msg"),
    (
        pytest.param(
            ["-I", "inventories/i_dont_exist"],
            "Unable to use inventories/i_dont_exist as an inventory source: no such file or directory",
            id="1",
        ),
        pytest.param(
            ["-I", "inventories/bad_inventory"],
            "Unable to parse inventories/bad_inventory as an inventory source",
            id="2",
        ),
    ),
)
def test_with_inventory_emit_warning(inventory_opts: list[str], error_msg: str) -> None:
    """Validate using --inventory can emit useful warnings about inventory files."""
    lintable = Lintable("examples/playbooks/test_using_inventory.yml")
    result = run_ansible_lint(lintable.filename, *inventory_opts)
    assert error_msg in result.stderr


def test_with_inventory_via_ansible_cfg(tmp_path: Path) -> None:
    """Validate using inventory file from ansible.cfg remedies syntax-check[specific] violation."""
    (tmp_path / "ansible.cfg").write_text("[defaults]\ninventory = foo\n")
    (tmp_path / "foo").write_text("[group_name]\nhost1\nhost2\n")
    lintable = Lintable(tmp_path / "playbook.yml")
    lintable.content = "---\n- name: Test\n  hosts:\n    - group_name\n  serial: \"{{ batch | default(groups['group_name'] | length) }}\"\n"
    lintable.kind = "playbook"
    lintable.write(force=True)

    result = run_ansible_lint(lintable.filename, cwd=tmp_path)
    assert result.returncode == RC.SUCCESS
