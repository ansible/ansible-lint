"""Tests related to prerun part of the linter."""
import os
from typing import List

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flaky import flaky

from ansiblelint import prerun
from ansiblelint.testing import run_ansible_lint


# https://github.com/box/flaky/issues/170
@flaky(max_runs=3)  # type: ignore
def test_prerun_reqs_v1() -> None:
    """Checks that the linter can auto-install requirements v1 when found."""
    cwd = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "examples", "reqs_v1"
        )
    )
    result = run_ansible_lint("-v", ".", cwd=cwd)
    assert "Running ansible-galaxy role install" in result.stderr, result.stderr
    assert (
        "Running ansible-galaxy collection install" not in result.stderr
    ), result.stderr
    assert result.returncode == 0, result


@flaky(max_runs=3)  # type: ignore
def test_prerun_reqs_v2() -> None:
    """Checks that the linter can auto-install requirements v2 when found."""
    cwd = os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "examples", "reqs_v2"
        )
    )
    result = run_ansible_lint("-v", ".", cwd=cwd)
    assert "Running ansible-galaxy role install" in result.stderr, result.stderr
    assert "Running ansible-galaxy collection install" in result.stderr, result.stderr
    assert result.returncode == 0, result


def test__update_env_no_old_value_no_default_no_value(monkeypatch: MonkeyPatch) -> None:
    """Make sure empty value does not touch environment."""
    monkeypatch.delenv("DUMMY_VAR", raising=False)

    prerun._update_env("DUMMY_VAR", [])

    assert "DUMMY_VAR" not in os.environ


def test__update_env_no_old_value_no_value(monkeypatch: MonkeyPatch) -> None:
    """Make sure empty value does not touch environment."""
    monkeypatch.delenv("DUMMY_VAR", raising=False)

    prerun._update_env("DUMMY_VAR", [], "a:b")

    assert "DUMMY_VAR" not in os.environ


def test__update_env_no_default_no_value(monkeypatch: MonkeyPatch) -> None:
    """Make sure empty value does not touch environment."""
    monkeypatch.setenv("DUMMY_VAR", "a:b")

    prerun._update_env("DUMMY_VAR", [])

    assert os.environ["DUMMY_VAR"] == "a:b"


@pytest.mark.parametrize(
    ("value", "result"),
    (
        (["a"], "a"),
        (["a", "b"], "a:b"),
        (["a", "b", "c"], "a:b:c"),
    ),
)
def test__update_env_no_old_value_no_default(
    monkeypatch: MonkeyPatch, value: List[str], result: str
) -> None:
    """Values are concatenated using : as the separator."""
    monkeypatch.delenv("DUMMY_VAR", raising=False)

    prerun._update_env("DUMMY_VAR", value)

    assert os.environ["DUMMY_VAR"] == result


@pytest.mark.parametrize(
    ("default", "value", "result"),
    (
        ("a:b", ["c"], "a:b:c"),
        ("a:b", ["c:d"], "a:b:c:d"),
    ),
)
def test__update_env_no_old_value(
    monkeypatch: MonkeyPatch, default: str, value: List[str], result: str
) -> None:
    """Values are appended to default value."""
    monkeypatch.delenv("DUMMY_VAR", raising=False)

    prerun._update_env("DUMMY_VAR", value, default)

    assert os.environ["DUMMY_VAR"] == result


@pytest.mark.parametrize(
    ("old_value", "value", "result"),
    (
        ("a:b", ["c"], "a:b:c"),
        ("a:b", ["c:d"], "a:b:c:d"),
    ),
)
def test__update_env_no_default(
    monkeypatch: MonkeyPatch, old_value: str, value: List[str], result: str
) -> None:
    """Values are appended to preexisting value."""
    monkeypatch.setenv("DUMMY_VAR", old_value)

    prerun._update_env("DUMMY_VAR", value)

    assert os.environ["DUMMY_VAR"] == result


@pytest.mark.parametrize(
    ("old_value", "default", "value", "result"),
    (
        ("", "", ["e"], "e"),
        ("a", "", ["e"], "a:e"),
        ("", "c", ["e"], "e"),
        ("a", "c", ["e:f"], "a:e:f"),
    ),
)
def test__update_env(
    monkeypatch: MonkeyPatch,
    old_value: str,
    default: str,
    value: List[str],
    result: str,
) -> None:
    """Defaults are ignored when preexisting value is present."""
    monkeypatch.setenv("DUMMY_VAR", old_value)

    prerun._update_env("DUMMY_VAR", value)

    assert os.environ["DUMMY_VAR"] == result
