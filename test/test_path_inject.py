"""Tests for path_inject() handling of symlinked PATH entries."""

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


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks")
def test_path_inject_own_location_not_duplicated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A venv bin that is both the interpreter and own location is added once."""
    real_bin, _ = _make_venv_with_symlink(tmp_path)
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.delenv("PYENV_VIRTUAL_ENV", raising=False)
    monkeypatch.setattr(sys, "executable", str(real_bin / "python"))

    path_inject(str(real_bin / "ansible-lint"))

    assert os.environ["PATH"].split(os.pathsep).count(str(real_bin)) == 1
    err = capsys.readouterr().err
    assert f"PATH altered to include {real_bin} ::" in err


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks")
def test_path_inject_own_location_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The own location is added when the interpreter directory has no ansible."""
    real_bin, _ = _make_venv_with_symlink(tmp_path)
    other_bin = tmp_path / "other" / "bin"
    other_bin.mkdir(parents=True)
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.delenv("PYENV_VIRTUAL_ENV", raising=False)
    monkeypatch.setattr(sys, "executable", str(other_bin / "python"))

    path_inject(str(real_bin / "ansible-lint"))

    assert os.environ["PATH"].split(os.pathsep) == [str(real_bin), "/usr/bin"]
