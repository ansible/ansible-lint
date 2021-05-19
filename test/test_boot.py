"""Test related to ansiblelint initialization."""
import sys
from subprocess import run

import pytest


@pytest.mark.parametrize('module', ("ansiblelint", "ansiblelint.__main__"))
def test_import(module: str) -> None:
    """Safeguard that Ansible does not become an implicit import."""
    # We cannot test it directly because our test fixtures already do
    # import Ansible, so we need to test this using a separated process.
    result = run(
        [
            sys.executable,
            "-c",
            f"import {module}, sys; sys.exit(0 if 'ansible' not in sys.modules else 1)",
        ],
        check=False,
    )
    assert result.returncode == 0
