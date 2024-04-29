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
    # "ERROR! the role 'this_role_is_missing' was not found in ROLE_INCLUDE_PATHS\n\nThe error appears to be in 'FILE_PATH': line 5, column 7, but may\nbe elsewhere in the file depending on the exact syntax problem.\n\nThe offending line appears to be:\n\n  roles:\n    - this_role_is_missing\n      ^ here\n"
    KnownError(
        tag="specific",
        regex=re.compile(
            r"^ERROR! (?P<title>the role '.*' was not found in[^\n]*)'(?P<filename>[\w\/\.\-]+)': line (?P<line>\d+), column (?P<column>\d+)",
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
