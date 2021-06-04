"""Rule definition for ansible syntax check."""
import json
import re
import subprocess
import sys
from typing import Any, List

from ansiblelint._internal.rules import BaseRule, RuntimeErrorRule
from ansiblelint.config import options
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.logger import timed_info
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.text import strip_ansi_escape

DESCRIPTION = """\
Running ``ansible-playbook --syntax-check ...`` failed.

This error **cannot be disabled** due to being a prerequisite for other steps.
You can either exclude these files from linting or better assure they can be
loaded by Ansible. This is often achieved by editing inventory file and/or
``ansible.cfg`` so ansible can load required variables.

If undefined variables are the failure reason you could use jinja default()
filter in order to provide fallback values.
"""

_ansible_syntax_check_re = re.compile(
    r"^ERROR! (?P<title>[^\n]*)\n\nThe error appears to be in "
    r"'(?P<filename>.*)': line (?P<line>\d+), column (?P<column>\d+)",
    re.MULTILINE | re.S | re.DOTALL,
)

_empty_playbook_re = re.compile(
    r"^ERROR! Empty playbook, nothing to do", re.MULTILINE | re.S | re.DOTALL
)


class AnsibleSyntaxCheckRule(AnsibleLintRule):
    """Ansible syntax check report failure."""

    id = "syntax-check"
    shortdesc = "Ansible syntax check failed"
    description = DESCRIPTION
    severity = "VERY_HIGH"
    tags = ["core", "unskippable"]
    version_added = "v5.0.0"

    @staticmethod
    def _get_ansible_syntax_check_matches(lintable: Lintable) -> List[MatchError]:
        """Run ansible syntax check and return a list of MatchError(s)."""
        if lintable.kind != 'playbook':
            return []

        with timed_info("Executing syntax check on %s", lintable.path):
            extra_vars_cmd = []
            if options.extra_vars:
                extra_vars_cmd = ['--extra-vars', json.dumps(options.extra_vars)]
            cmd = [
                'ansible-playbook',
                '--syntax-check',
                *extra_vars_cmd,
                str(lintable.path),
            ]
            run = subprocess.run(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,  # needed when command is a list
                universal_newlines=True,
                check=False,
            )
            result = []
        if run.returncode != 0:
            message = None
            filename = str(lintable.path)
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

            m = _ansible_syntax_check_re.search(stderr)
            if m:
                message = m.groupdict()['title']
                # Ansible returns absolute paths
                filename = m.groupdict()['filename']
                linenumber = int(m.groupdict()['line'])
                column = int(m.groupdict()['column'])
            elif _empty_playbook_re.search(stderr):
                message = "Empty playbook, nothing to do"
                filename = str(lintable.path)
                tag = "empty-playbook"

            if run.returncode == 4:
                rule: BaseRule = AnsibleSyntaxCheckRule()
            else:
                rule = RuntimeErrorRule()
                if not message:
                    message = (
                        f"Unexpected error code {run.returncode} from "
                        f"execution of: {' '.join(cmd)}"
                    )

            result.append(
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
        return result


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    def test_get_ansible_syntax_check_matches() -> None:
        """Validate parsing of ansible output."""
        lintable = Lintable(
            'examples/playbooks/conflicting_action.yml', kind='playbook'
        )
        result = AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(lintable)
        assert result[0].linenumber == 3
        assert result[0].column == 7
        assert result[0].message == "conflicting action statements: debug, command"
        # We internally convert absolute paths returned by ansible into paths
        # relative to current directory.
        assert result[0].filename.endswith("/conflicting_action.yml")
        assert len(result) == 1

    def test_empty_playbook() -> None:
        """Validate detection of empty-playbook."""
        lintable = Lintable('examples/playbooks/empty_playbook.yml', kind='playbook')
        result = AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(lintable)
        assert result[0].linenumber == 1
        # We internally convert absolute paths returned by ansible into paths
        # relative to current directory.
        assert result[0].filename.endswith("/empty_playbook.yml")
        assert result[0].tag == "empty-playbook"
        assert result[0].message == "Empty playbook, nothing to do"
        assert len(result) == 1

    def test_extra_vars_passed_to_command(config_options: Any) -> None:
        """Validate `extra-vars` are passed to syntax check command."""
        config_options.extra_vars = {
            'foo': 'bar',
            'complex_variable': ':{;\t$()',
        }
        lintable = Lintable('examples/playbooks/extra_vars.yml', kind='playbook')

        result = AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(lintable)

        assert not result
