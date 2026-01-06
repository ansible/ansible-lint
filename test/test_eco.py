"""Slow ecosystem tests."""

import os
import pathlib
import sys
from subprocess import run

import pytest
from ansible_compat.runtime import Runtime
from packaging.version import Version

runtime = Runtime()


@pytest.mark.eco
@pytest.mark.skipif(
    sys.version_info < (3, 13) or runtime.version < Version("2.20"),
    reason="Skipping eco tests with ansible-core < 2.20 or python < 3.13 as outputs are different.",
)
@pytest.mark.parametrize(
    "repo",
    (
        "ansible-docker-rootless",
        "ansible-role-hardening",
        "ansible-role-mysql",
        "ansible_collection_system",
        "bootstrap",
        "cisco.nxos",
    ),
)
def test_eco(repo: str) -> None:
    """Test linter against a 3rd party repository."""
    proc = run(
        [
            "ansible-lint",
            "--offline",
            "-qq",
            "--generate-ignore",
            "--format=codeclimate",
        ],
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
    pathlib.Path(f"test/fixtures/eco/{repo}.stderr").write_text(
        proc.stdout, encoding="utf-8"
    )
    pathlib.Path(f"test/fixtures/eco/{repo}.rc").write_text(
        str(proc.returncode), encoding="utf-8"
    )
    run(["git", "diff", "--exit-code"], check=True)
