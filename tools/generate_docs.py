#!python3
"""Script that tests rule markdown documentation."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ansiblelint.cli import get_rules_dirs
from ansiblelint.config import Options
from ansiblelint.rules import (
    RulesCollection,
    TransformMixin,
)

if __name__ == "__main__":
    subprocess.run(
        ["ansible-lint", "--list-rules"],  # noqa: S607
        check=True,
        stdout=subprocess.DEVNULL,
    )

    file = Path("docs/_autofix_rules.md")
    options = Options()
    options.rulesdirs = get_rules_dirs([])
    options.list_rules = True
    rules = RulesCollection(
        options.rulesdirs,
        options=options,
    )
    contents: list[str] = [
        f"- [{rule.id}](rules/{rule.id}.md)\n"
        for rule in rules.alphabetical()
        if issubclass(rule.__class__, TransformMixin)
    ]

    # Write the injected contents to the file.
    with file.open(encoding="utf-8", mode="w") as fh:
        fh.writelines(contents)
