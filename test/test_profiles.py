"""Tests for the --profile feature."""
import platform
import subprocess
import sys

from _pytest.capture import CaptureFixture

from ansiblelint.rules import RulesCollection, filter_rules_with_profile
from ansiblelint.rules.risky_shell_pipe import ShellWithoutPipefail
from ansiblelint.text import strip_ansi_escape


def test_profile_min() -> None:
    """Asserts our ability to unload rules based on profile."""
    collection = RulesCollection()
    assert len(collection.rules) == 4, "Unexpected number of implicit rules."
    # register one extra rule that we know not to be part of "min" profile

    collection.register(ShellWithoutPipefail())
    assert len(collection.rules) == 5, "Failed to register new rule."

    filter_rules_with_profile(collection.rules, "min")
    assert (
        len(collection.rules) == 3
    ), "Failed to unload rule that is not part of 'min' profile."


def test_profile_listing(capfd: CaptureFixture[str]) -> None:
    """Test that run without arguments it will detect and lint the entire repository."""
    cmd = [
        sys.executable,
        "-m",
        "ansiblelint",
        "-P",
    ]
    result = subprocess.run(cmd, check=False).returncode
    assert result == 0

    out, err = capfd.readouterr()

    # Confirmation that it runs in auto-detect mode
    assert "command-instead-of-module" in out
    # On WSL we might see this warning on stderr:
    # [WARNING]: Ansible is being run in a world writable directory
    # WSL2 has "WSL2" in platform name but WSL1 has "microsoft":
    platform_name = platform.platform().lower()
    err_lines = []
    for line in strip_ansi_escape(err).splitlines():
        if "SyntaxWarning:" in line:
            continue
        if (
            "Skipped installing collection dependencies due to running in offline mode."
            in line
        ):
            continue
        err_lines.append(line)
    if all(word not in platform_name for word in ["wsl", "microsoft"]) and err_lines:
        assert (
            not err_lines
        ), f"Unexpected stderr output found while running on {platform_name} platform:\n{err_lines}"
