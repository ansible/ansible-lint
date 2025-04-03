"""Rule definition for ansible syntax check."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.types import ansible_error_format


@dataclass
class KnownError:
    """Class that tracks result of linting."""

    tag: str
    regex: re.Pattern[str]


if ansible_error_format == 1:
    _ansible_error_prefix = "ERROR! "
    _ansible_error_detail = r"\n\nThe error appears to be in '(?P<filename>[\w\/\.\-]+)': line (?P<line>\d+), column (?P<column>\d+)"
elif ansible_error_format == 2:  # 2.19 with data tagging
    _ansible_error_prefix = r"\[ERROR\]: "
    _ansible_error_detail = (
        r"\nOrigin: (?P<filename>[\w\/\.\-]+):(?P<line>\d+):(?P<column>\d+)"
    )
else:  # pragma: no cover
    msg = f"Unsupported ansible_error_format: {ansible_error_format}"
    raise NotImplementedError(msg)

# Order matters, we only report the first matching pattern, the one at the end
# is used to match generic or less specific patterns.
OUTPUT_PATTERNS = (
    KnownError(
        tag="missing-file",
        regex=re.compile(
            # do not use <filename> capture group for this because we want to report original file, not the missing target one
            r"(?P<title>Unable to retrieve file contents)\n(?P<details>Could not find or access '(?P<value>.*)'[^\n]*)",
            re.MULTILINE | re.DOTALL | re.DOTALL,
        ),
    ),
    KnownError(
        tag="no-file",
        regex=re.compile(
            rf"^{_ansible_error_prefix}(?P<title>No file specified for [^\n]*){_ansible_error_detail}",
            re.MULTILINE | re.DOTALL | re.DOTALL,
        ),
    ),
    KnownError(
        tag="empty-playbook",
        regex=re.compile(
            r"Empty playbook, nothing to do",
            re.MULTILINE | re.DOTALL | re.DOTALL,
        ),
    ),
    KnownError(
        tag="malformed",
        regex=re.compile(
            rf"^(statically imported: (?P<filename>[\w\/\.\-]+)\n)?{_ansible_error_prefix}(?P<title>A malformed block was encountered while loading a block[^\n]*)",
            re.MULTILINE | re.DOTALL | re.DOTALL,
        ),
    ),
    KnownError(
        tag="unknown-module",
        regex=re.compile(
            rf"^{_ansible_error_prefix}(?P<title>couldn't resolve module/action [^\n]*){_ansible_error_detail}",
            re.MULTILINE | re.DOTALL | re.DOTALL,
        ),
    ),
    KnownError(
        tag="specific",
        regex=re.compile(
            rf"^{_ansible_error_prefix}(?P<title>[^\n]*){_ansible_error_detail}",
            re.MULTILINE | re.DOTALL | re.DOTALL,
        ),
    ),
    # "ERROR! the role 'this_role_is_missing' was not found in ROLE_INCLUDE_PATHS\n\nThe error appears to be in 'FILE_PATH': line 5, column 7, but may\nbe elsewhere in the file depending on the exact syntax problem.\n\nThe offending line appears to be:\n\n  roles:\n    - this_role_is_missing\n      ^ here\n"
    KnownError(
        tag="specific",
        regex=re.compile(
            rf"^{_ansible_error_prefix}(?P<title>the role '.*' was not found in[^\n]*){_ansible_error_detail}",
            re.MULTILINE | re.DOTALL | re.DOTALL,
        ),
    ),
    # 2.19:
    # [ERROR]: no module/action detected in task.
    # Origin: /Users/ssbarnea/code/a/ansible-lint/examples/roles/invalid_due_syntax/tasks/main.yml:2:3
    # KnownError(
    #     tag="specific",
    #     regex=re.compile(
    #         r"^\[ERROR\]: (?P<title>[^\n]*)\nOrigin: (?P<filename>[\w\/\.\-]+):(?P<line>\d+):(?P<column>\d+)",
    #         re.MULTILINE | re.DOTALL | re.DOTALL,
    #     ),
    # ),
)


class AnsibleSyntaxCheckRule(AnsibleLintRule):
    """Ansible syntax check failed."""

    id = "syntax-check"
    severity = "VERY_HIGH"
    tags = ["core", "unskippable"]
    version_changed = "5.0.0"
    _order = 0
