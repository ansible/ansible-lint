"""Validates linter behavior when ansible python package is missing."""
from subprocess import run

if __name__ == "__main__":
    cmd = ["ansible-lint", "--version"]
    result = run(cmd, check=False)
    assert result.returncode == 4  # missing ansible
