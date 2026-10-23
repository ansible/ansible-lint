"""Tests for path_inject() handling of PATH entries and tool environments."""

import os
import sys
from pathlib import Path

import pytest

from ansiblelint.__main__ import path_inject


def _make_venv_with_symlink(tmp_path: Path) -> tuple[Path, Path]:
    real_bin = tmp_path / "real" / "venv" / "bin"
    real_bin.mkdir(parents=True)
    ansible = real_bin / "ansible"
    ansible.touch()
    ansible.chmod(0o755)
    (tmp_path / "link").symlink_to(tmp_path / "real", target_is_directory=True)
    return real_bin, tmp_path / "link" / "venv" / "bin"


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks")
def test_path_inject_symlinked_path_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A venv bin reached through a symlink must not trigger a PATH warning."""
    real_bin, link_bin = _make_venv_with_symlink(tmp_path)
    path_value = os.pathsep.join([str(link_bin), "/usr/bin"])
    monkeypatch.setenv("PATH", path_value)
    monkeypatch.delenv("PYENV_VIRTUAL_ENV", raising=False)
    monkeypatch.setattr(sys, "executable", str(real_bin / "python"))

    path_inject()

    assert "PATH altered to include" not in capsys.readouterr().err
    assert os.environ["PATH"] == path_value


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks")
def test_path_inject_symlinked_tilde_path_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ~-prefixed PATH entry reached through a symlink must not be duplicated."""
    real_bin, _ = _make_venv_with_symlink(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", os.pathsep.join(["~/link/venv/bin", "/usr/bin"]))
    monkeypatch.delenv("PYENV_VIRTUAL_ENV", raising=False)
    monkeypatch.setattr(sys, "executable", str(real_bin / "python"))

    path_inject()

    assert "PATH altered to include" not in capsys.readouterr().err
    assert os.environ["PATH"].split(os.pathsep).count(str(real_bin)) == 0


def _make_uv_tool_env(tmp_path: Path) -> Path:
    """Lay out what uv tool install leaves behind, outside its default tools dir."""
    env = tmp_path / "installs" / "ansible-lint"
    bin_dir = env / "bin"
    bin_dir.mkdir(parents=True)
    for name in ("python", "ansible"):
        exe = bin_dir / name
        exe.touch()
        exe.chmod(0o755)
    (env / "uv-receipt.toml").write_text(
        '[tool]\nrequirements = [{ name = "ansible-lint" }]\n',
    )
    return bin_dir


def test_path_inject_uv_tool_env_outside_tools_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A uv tool environment is recognized by its receipt, wherever it lives."""
    bin_dir = _make_uv_tool_env(tmp_path)
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.delenv("PYENV_VIRTUAL_ENV", raising=False)
    monkeypatch.setattr(sys, "executable", str(bin_dir / "python"))

    path_inject()

    assert "PATH altered to include" not in capsys.readouterr().err
    assert os.environ["PATH"].split(os.pathsep)[0] == bin_dir.as_posix()


def test_path_inject_plain_venv_still_warns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without the receipt, the same layout is a plain venv and still warns."""
    bin_dir = _make_uv_tool_env(tmp_path)
    (bin_dir.parent / "uv-receipt.toml").unlink()
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.delenv("PYENV_VIRTUAL_ENV", raising=False)
    monkeypatch.setattr(sys, "executable", str(bin_dir / "python"))

    path_inject()

    assert "PATH altered to include" in capsys.readouterr().err
