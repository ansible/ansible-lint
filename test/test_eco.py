"""Slow ecosystem tests."""

import os
import pathlib
from subprocess import run

import pytest


@pytest.mark.eco
@pytest.mark.parametrize(
    "repo",
    (
        "ansible-docker-rootless",
        "ansible-role-hardening",
        "ansible-role-mysql",
        "ansible_collection_system",
        "bootstrap",
        "cisco.nxos",
        "debops",
    ),
)
def test_eco(repo: str) -> None:
    """Test linter against a 3rd party repository."""
    proc = run(
        ["ansible-lint", "-qq", "--generate-ignore", "--format=codeclimate"],
        text=True,
        capture_output=True,
        check=False,
        shell=True,
        cwd=f"test/fixtures/eco/{repo}",
        env={
            **os.environ,
            "NO_COLOR": "1",
            "ANSIBLE_LINT_IGNORE_FILE": f"test/fixtures/eco/{repo}.ignore.txt",
        },
    )
    pathlib.Path(f"test/fixtures/eco/{repo}.json").write_text(
        proc.stdout, encoding="utf-8"
    )
    assert proc.returncode == 0
    run(["git", "diff", "--exit-code"], check=True)
