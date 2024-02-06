"""Test for app module."""

from pathlib import Path

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
