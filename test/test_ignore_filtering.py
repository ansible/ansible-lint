"""Tests for ignore file filtering functionality."""

import re
from pathlib import Path

from ansiblelint.testing import run_ansible_lint


def test_ignore_exact_match_filters_violation(tmp_path: Path) -> None:
    """Test that exact file path in ignore file filters violations."""
    # Create a playbook with a violation
    playbook = tmp_path / "playbook.yml"
    playbook.write_text(
        "---\n"
        "- name: Test\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: Install package\n"
        "      ansible.builtin.package:\n"
        "        name: nginx\n"
        "        state: latest\n",
        encoding="utf-8",
    )

    # First, verify the violation exists without ignore file
    result = run_ansible_lint(str(playbook), cwd=tmp_path)
    assert result.returncode != 0
    assert "package-latest" in result.stdout

    # Create ignore file with exact path
    ignore_file = tmp_path / ".ansible-lint-ignore"
    ignore_file.write_text("playbook.yml package-latest\n", encoding="utf-8")

    pattern = r"^package-latest.*# ignored"

    # Now the violation should be filtered
    result = run_ansible_lint(str(playbook), cwd=tmp_path)
    assert result.returncode == 0
    assert re.match(pattern, result.stdout) is not None


def test_ignore_wildcard_pattern_filters_violation(tmp_path: Path) -> None:
    """Test that wildcard patterns in ignore file filter violations."""
    # Create a role task file with a violation
    role_task = tmp_path / "roles" / "webserver" / "tasks" / "main.yml"
    role_task.parent.mkdir(parents=True)
    role_task.write_text(
        "---\n"
        "- name: Task without changed_when\n"
        "  ansible.builtin.command: echo hello\n",
        encoding="utf-8",
    )

    # First, verify the violation exists without ignore file
    result = run_ansible_lint(str(role_task), cwd=tmp_path)
    assert result.returncode != 0
    assert "no-changed-when" in result.stdout

    # Create ignore file with wildcard pattern
    ignore_file = tmp_path / ".ansible-lint-ignore"
    ignore_file.write_text("roles/*/tasks/*.yml no-changed-when", encoding="utf-8")

    # Now the violation should be filtered by pattern
    result = run_ansible_lint(str(role_task), cwd=tmp_path)
    assert result.returncode == 0
    assert re.search(r"^no-changed-when.*# ignored", result.stdout)


def test_ignore_recursive_pattern_filters_violation(tmp_path: Path) -> None:
    """Test that recursive glob patterns in ignore file filter violations."""
    # Create a role task file with a violation
    role_task = tmp_path / "roles" / "webserver" / "tasks" / "main.yml"
    role_task.parent.mkdir(parents=True)
    role_task.write_text(
        "---\n"
        "- name: Task without changed_when\n"
        "  ansible.builtin.command: echo hello\n",
        encoding="utf-8",
    )

    # Create ignore file with wildcard pattern
    ignore_file = tmp_path / ".ansible-lint-ignore"
    ignore_file.write_text("**/*.yml no-changed-when", encoding="utf-8")

    # Now the violation should be filtered by pattern
    result = run_ansible_lint(str(role_task), cwd=tmp_path)
    assert result.returncode == 0
    assert re.search(r"^no-changed-when.*# ignored", result.stdout)


def test_ignore_mix_exact_and_patterns(tmp_path: Path) -> None:
    """Test mixing exact paths and patterns in ignore file."""
    # Create a specific playbook with violation
    site_yml = tmp_path / "site.yml"
    site_yml.write_text(
        "---\n"
        "- name: Install package\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: Install latest\n"
        "      ansible.builtin.package:\n"
        "        name: nginx\n"
        "        state: latest\n",
        encoding="utf-8",
    )

    # Create a role task file with a violation
    role_task = tmp_path / "roles" / "webserver" / "tasks" / "main.yml"
    role_task.parent.mkdir(parents=True)
    role_task.write_text(
        "---\n"
        "- name: Task without changed_when\n"
        "  ansible.builtin.command: echo hello\n",
        encoding="utf-8",
    )

    # First, verify the violation exists without ignore file
    result = run_ansible_lint(str(site_yml), str(role_task), cwd=tmp_path)
    assert result.returncode != 0
    assert "package-latest" in result.stdout
    assert "no-changed-when" in result.stdout

    # Create ignore file with wildcard pattern
    ignore_file = tmp_path / ".ansible-lint-ignore"
    ignore_file.write_text(
        "site.yml package-latest\nroles/*/tasks/*.yml no-changed-when\n",
        encoding="utf-8",
    )

    # Now the violation should be filtered by pattern
    result = run_ansible_lint(str(site_yml), str(role_task), cwd=tmp_path)
    assert result.returncode == 0
    assert re.search(r"package-latest.*# ignored", result.stdout)
    assert re.search(r"no-changed-when.*# ignored", result.stdout)


def test_ignore_pattern_no_match_keeps_violation(tmp_path: Path) -> None:
    """Test that violations are NOT ignored when pattern doesn't match."""
    # Create a specific playbook with violation
    site_yml = tmp_path / "site.yml"
    site_yml.write_text(
        "---\n"
        "- name: Install package\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: Install latest\n"
        "      ansible.builtin.package:\n"
        "        name: nginx\n"
        "        state: latest\n",
        encoding="utf-8",
    )

    ignore_file = tmp_path / ".ansible-lint-ignore"
    ignore_file.write_text("roles/*/tasks/*.yml package-latest\n", encoding="utf-8")

    result = run_ansible_lint(str(site_yml), cwd=tmp_path)
    assert result.returncode != 0
    assert "package-latest" in result.stdout
    assert not re.search(r"package-latest.*# ignored", result.stdout)


def test_ignore_multiple_patterns_same_file(tmp_path: Path) -> None:
    """Test when multiple patterns match the same file."""
    # Create a specific playbook with violation
    role_task = tmp_path / "roles" / "webserver" / "tasks" / "main.yml"
    role_task.parent.mkdir(parents=True)
    role_task.write_text(
        "---\n- name: Task without changed_when\n  command: echo hello\n",
        encoding="utf-8",
    )

    ignore_file = tmp_path / ".ansible-lint-ignore"
    ignore_file.write_text(
        "roles/*/tasks/*.yml fqcn[action-core]\nroles/*/tasks/*.yml no-changed-when\n",
        encoding="utf-8",
    )

    result = run_ansible_lint(str(role_task), cwd=tmp_path)
    assert result.returncode == 0
    assert re.search(r"fqcn\[action-core\].*# ignored", result.stdout)
    assert re.search(r"no-changed-when.*# ignored", result.stdout)


def test_ignore_with_skip_qualifier_removes_match(tmp_path: Path) -> None:
    """Test that violations with skip qualifier are removed from output."""
    # Create a playbook with a violation
    playbook = tmp_path / "playbook.yml"
    playbook.write_text(
        "---\n"
        "- name: Test\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: Install package\n"
        "      ansible.builtin.package:\n"
        "        name: nginx\n"
        "        state: latest\n",
        encoding="utf-8",
    )

    # Create ignore file with exact path
    ignore_file = tmp_path / ".ansible-lint-ignore"
    ignore_file.write_text("playbook.yml package-latest skip\n", encoding="utf-8")

    # Now the violation should be filtered
    result = run_ansible_lint(str(playbook), cwd=tmp_path)
    assert result.returncode == 0
    assert "package-latest" not in result.stdout


def test_ignore_wildcard_pattern_with_skip_qualifier_removes_match(
    tmp_path: Path,
) -> None:
    """Test that wildcard pattern violations with skip qualifier are removed from output."""
    # Create a role task file with a violation
    role_task = tmp_path / "roles" / "webserver" / "tasks" / "main.yml"
    role_task.parent.mkdir(parents=True)
    role_task.write_text(
        "---\n"
        "- name: Task without changed_when\n"
        "  ansible.builtin.command: echo hello\n",
        encoding="utf-8",
    )

    # Create ignore file with exact path
    ignore_file = tmp_path / ".ansible-lint-ignore"
    ignore_file.write_text(
        "roles/*/tasks/*.yml no-changed-when skip\n", encoding="utf-8"
    )

    # Now the violation should be filtered
    result = run_ansible_lint(str(role_task), cwd=tmp_path)
    assert result.returncode == 0
    assert "no-changed-when" not in result.stdout
