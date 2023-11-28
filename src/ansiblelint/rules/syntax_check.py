"""Rule definition for ansible syntax check."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ansiblelint.rules import AnsibleLintRule


@dataclass
class KnownError:
    """Class that tracks result of linting."""

    tag: str
    regex: re.Pattern[str]


# Order matters, we only report the first matching pattern, the one at the end
# is used to match generic or less specific patterns.
OUTPUT_PATTERNS = (
    KnownError(
        tag="missing-file",
        regex=re.compile(
            # do not use <filename> capture group for this because we want to report original file, not the missing target one
            r"(?P<title>Unable to retrieve file contents)\n(?P<details>Could not find or access '(?P<value>.*)'[^\n]*)",
            re.MULTILINE | re.S | re.DOTALL,
        ),
    ),
    KnownError(
        tag="empty-playbook",
        regex=re.compile(
            "Empty playbook, nothing to do",
            re.MULTILINE | re.S | re.DOTALL,
        ),
    ),
    KnownError(
        tag="malformed",
        regex=re.compile(
            "^ERROR! (?P<title>A malformed block was encountered while loading a block[^\n]*)",
            re.MULTILINE | re.S | re.DOTALL,
        ),
    ),
    KnownError(
        tag="unknown-module",
        regex=re.compile(
            r"^ERROR! (?P<title>couldn't resolve module/action [^\n]*)\n\nThe error appears to be in '(?P<filename>[\w\/\.\-]+)': line (?P<line>\d+), column (?P<column>\d+)",
            re.MULTILINE | re.S | re.DOTALL,
        ),
    ),
    KnownError(
        tag="specific",
        regex=re.compile(
            r"^ERROR! (?P<title>[^\n]*)\n\nThe error appears to be in '(?P<filename>[\w\/\.\-]+)': line (?P<line>\d+), column (?P<column>\d+)",
            re.MULTILINE | re.S | re.DOTALL,
        ),
    ),
)


class AnsibleSyntaxCheckRule(AnsibleLintRule):
    """Ansible syntax check failed."""

    id = "syntax-check"
    severity = "VERY_HIGH"
    tags = ["core", "unskippable"]
    version_added = "v5.0.0"
    _order = 0
