"""Validates linter behavior when ansible python package is missing."""
import os
import subprocess

if __name__ == "__main__":
    cmd = ["ansible-lint", "--version"]
    result = subprocess.run(
        cmd,
        universal_newlines=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ,
    )
    assert result.returncode == 4, result  # missing ansible
