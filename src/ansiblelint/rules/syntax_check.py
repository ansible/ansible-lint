"""Rule definition for ansible syntax check."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from ansiblelint._internal.rules import BaseRule, RuntimeErrorRule, WarningRule
from ansiblelint.app import get_app
from ansiblelint.config import options
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.logger import timed_info
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.text import strip_ansi_escape


@dataclass
class KnownError:
    """Class that tracks result of linting."""

    tag: str
    regex: re.Pattern[str]


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
        tag="specific",
        regex=re.compile(
            r"^ERROR! (?P<title>[^\n]*)\n\nThe error appears to be in '(?P<filename>.*)': line (?P<line>\d+), column (?P<column>\d+)",
            re.MULTILINE | re.S | re.DOTALL,
        ),
    ),
    KnownError(
        tag="empty-playbook",
        regex=re.compile(
            "Empty playbook, nothing to do", re.MULTILINE | re.S | re.DOTALL
        ),
    ),
    KnownError(
        tag="malformed",
        regex=re.compile(
            "^ERROR! (?P<title>A malformed block was encountered while loading a block[^\n]*)",
            re.MULTILINE | re.S | re.DOTALL,
        ),
    ),
)


class AnsibleSyntaxCheckRule(AnsibleLintRule):
    """Ansible syntax check failed."""

    id = "syntax-check"
    severity = "VERY_HIGH"
    tags = ["core"]
    version_added = "v5.0.0"
    _order = 0

    @staticmethod
    # pylint: disable=too-many-locals
    def _get_ansible_syntax_check_matches(lintable: Lintable) -> list[MatchError]:
        """Run ansible syntax check and return a list of MatchError(s)."""
        default_rule: BaseRule = AnsibleSyntaxCheckRule()
        results = []
        if lintable.kind != "playbook":
            return []

        with timed_info("Executing syntax check on %s", lintable.path):
            # To avoid noisy warnings we pass localhost as current inventory:
            # [WARNING]: No inventory was parsed, only implicit localhost is available
            # [WARNING]: provided hosts list is empty, only localhost is available. Note that the implicit localhost does not match 'all'
            args = ["-i", "localhost,"]
            if options.extra_vars:
                args.extend(["--extra-vars", json.dumps(options.extra_vars)])
            cmd = [
                "ansible-playbook",
                "--syntax-check",
                *args,
                str(lintable.path.expanduser()),
            ]

            # To reduce noisy warnings like
            # CryptographyDeprecationWarning: Blowfish has been deprecated
            # https://github.com/paramiko/paramiko/issues/2038
            env = get_app().runtime.environ.copy()
            env["PYTHONWARNINGS"] = "ignore"

            run = subprocess.run(
                cmd,
                stdin=subprocess.PIPE,
                capture_output=True,
                shell=False,  # needed when command is a list
                text=True,
                check=False,
                env=env,
            )

        if run.returncode != 0:
            message = None
            filename = lintable
            linenumber = 1
            column = None
            tag = None

            stderr = strip_ansi_escape(run.stderr)
            stdout = strip_ansi_escape(run.stdout)
            if stderr:
                details = stderr
                if stdout:
                    details += "\n" + stdout
            else:
                details = stdout

            for pattern in OUTPUT_PATTERNS:
                rule = default_rule
                match = re.search(pattern.regex, stderr)
                if match:
                    groups = match.groupdict()
                    title = groups.get("title", match.group(0))
                    details = groups.get("details", "")
                    linenumber = int(groups.get("line", 1))

                    if "filename" in groups:
                        filename = Lintable(groups["filename"])
                    else:
                        filename = lintable
                    column = int(groups.get("column", 1))

                    if pattern.tag == "empty-playbook":
                        rule = WarningRule()

                    results.append(
                        MatchError(
                            message=title,
                            filename=filename,
                            linenumber=linenumber,
                            column=column,
                            rule=rule,
                            details=details,
                            tag=f"{rule.id}[{pattern.tag}]",
                        )
                    )

            if not results:
                rule = RuntimeErrorRule()
                message = (
                    f"Unexpected error code {run.returncode} from "
                    f"execution of: {' '.join(cmd)}"
                )
                results.append(
                    MatchError(
                        message=message,
                        filename=filename,
                        linenumber=linenumber,
                        column=column,
                        rule=rule,
                        details=details,
                        tag=tag,
                    )
                )

        return results


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    def test_get_ansible_syntax_check_matches() -> None:
        """Validate parsing of ansible output."""
        lintable = Lintable(
            "examples/playbooks/conflicting_action.yml", kind="playbook"
        )
        # pylint: disable=protected-access
        result = AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(lintable)
        assert result[0].linenumber == 4
        assert result[0].column == 7
        assert (
            result[0].message
            == "conflicting action statements: ansible.builtin.debug, ansible.builtin.command"
        )
        # We internally convert absolute paths returned by ansible into paths
        # relative to current directory.
        assert result[0].filename.endswith("/conflicting_action.yml")
        assert len(result) == 1

    def test_empty_playbook() -> None:
        """Validate detection of empty-playbook."""
        lintable = Lintable("examples/playbooks/empty_playbook.yml", kind="playbook")
        # pylint: disable=protected-access
        result = AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(lintable)
        assert result[0].linenumber == 1
        # We internally convert absolute paths returned by ansible into paths
        # relative to current directory.
        assert result[0].filename.endswith("/empty_playbook.yml")
        assert result[0].tag == "warning[empty-playbook]"
        assert result[0].message == "Empty playbook, nothing to do"
        assert len(result) == 1

    def test_extra_vars_passed_to_command(config_options: Any) -> None:
        """Validate `extra-vars` are passed to syntax check command."""
        config_options.extra_vars = {
            "foo": "bar",
            "complex_variable": ":{;\t$()",
        }
        lintable = Lintable("examples/playbooks/extra_vars.yml", kind="playbook")

        # pylint: disable=protected-access
        result = AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(lintable)

        assert not result
