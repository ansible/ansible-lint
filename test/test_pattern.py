"""Tests for the pattern feature."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LINT_BIN = Path(sys.executable).parent / "ansible-lint"


def test_creator_scaffolded_pattern() -> None:
    """Validate creator scaffolded pattern.

    Scaffold a pattern using ansible-creator. Run ansible-lint
    on the scaffolded pattern and validate lint results.

    Args:
        monkeypatch: Monkeypatch fixture.
    """
    # Create a tmp dir and copy an existing collection into it
    collection_src = Path("examples/collections/broken_no_runtime")
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_dest = Path(tmpdir) / collection_src.name
        shutil.copytree(collection_src, collection_dest)

        # Scaffold a pattern using ansible-creator
        result = subprocess.run(
            [
                "ansible-creator",
                "add",
                "resource",
                "pattern",
                "sample_pattern",
                collection_dest,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Pattern scaffolding failed: {result.stderr}"

        # Run ansible-lint on the scaffolded pattern
        pattern_path = collection_dest

        lint_result = subprocess.run(
            [str(LINT_BIN), pattern_path],
            capture_output=True,
            text=True,
            env={"NO_COLOR": "1"},
            check=False,
        )
        assert lint_result.returncode == 0, f"ansible-lint failed: {lint_result.stderr}"
