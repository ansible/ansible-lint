"""Test for app module."""
from pathlib import Path

from ansiblelint.file_utils import Lintable
from ansiblelint.testing import run_ansible_lint


def test_generate_ignore(tmp_path: Path) -> None:
    """Validate that --generate-ignore dumps expected ignore to the file."""
    lintable = Lintable(tmp_path / "vars.yaml")
    lintable.content = "foo: bar\nfoo: baz\n"
    lintable.write(force=True)
    assert not (tmp_path / ".ansible-lint-ignore").exists()
    result = run_ansible_lint(lintable.filename, "--generate-ignore", cwd=str(tmp_path))
    assert result.returncode == 2
    assert (tmp_path / ".ansible-lint-ignore").exists()
    with open(tmp_path / ".ansible-lint-ignore", encoding="utf-8") as f:
        assert "vars.yaml yaml[key-duplicates]\n" in f.readlines()
    # Run again and now we expect to succeed as we have an ignore file.
    result = run_ansible_lint(lintable.filename, cwd=str(tmp_path))
    assert result.returncode == 0
