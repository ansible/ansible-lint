"""Rule definition for ansible syntax check."""
import json
import logging
import re
import subprocess
import sys
from typing import Any, List, Optional, Union

from subprocess_tee import CompletedProcess

from ansiblelint._internal.rules import BaseRule, RuntimeErrorRule
from ansiblelint.app import get_app
from ansiblelint.config import options
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.logger import timed_info
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.text import strip_ansi_escape

_logger = logging.getLogger(__name__)
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
    """Ansible syntax check failed."""

    id = "syntax-check"
    description = DESCRIPTION
    severity = "VERY_HIGH"
    tags = ["core", "unskippable"]
    version_added = "v5.0.0"

    # pylint: disable=too-many-arguments
    @classmethod
    def _get_match(
        cls,
        run: CompletedProcess,
        message: Union[str, None],
        cmd: List[str],
        filename: str,
        linenumber: int = 1,
        column: Optional[int] = None,
        details: str = "",
        tag: Optional[str] = None,
    ) -> MatchError:
        """."""
        if run.returncode == 4:
            rule: BaseRule = AnsibleSyntaxCheckRule()
            if _empty_playbook_re.search(strip_ansi_escape(run.stderr)):
                message = "Empty playbook, nothing to do"
                tag = "empty-playbook"
        else:
            rule = RuntimeErrorRule()
            if not message:
                message = (
                    f"Unexpected error code {run.returncode} from "
                    f"execution of: {' '.join(cmd)}"
                )
        return MatchError(
            message=message,
            filename=filename,
            linenumber=linenumber,
            column=column,
            rule=rule,
            details=details,
            tag=tag,
        )

    # pylint: disable=too-many-locals,too-many-branches
    @staticmethod
    def _get_ansible_syntax_check_matches(  # noqa: C901
        lintables: List[Lintable],
    ) -> List[MatchError]:
        """Run ansible syntax check and return a list of MatchError(s)."""
        result: List[MatchError] = []
        playbook_paths = []

        for lintable in lintables:
            if lintable.kind == "playbook":
                playbook_paths.append(str(lintable.path))

        with timed_info("Executing syntax check on %s", ", ".join(playbook_paths)):
            extra_vars_cmd = []
            if options.extra_vars:
                extra_vars_cmd = ["--extra-vars", json.dumps(options.extra_vars)]
            cmd = [
                "ansible-playbook",
                "--syntax-check",
                "-i",  # avoids misleading warning
                "localhost,",
                *extra_vars_cmd,
                *playbook_paths,
            ]
            env = get_app().runtime.environ
            # avoid potentially distracting noisy warnings from ansible-playbook:
            env["ANSIBLE_DEPRECATION_WARNINGS"] = "False"
            env["ANSIBLE_DEVEL_WARNING"] = "False"
            env["PYTHONWARNINGS"] = "ignore"
            run = subprocess.run(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,  # needed when command is a list
                universal_newlines=True,
                check=False,
                env=env,
            )

        if run.returncode != 0:
            message = None
            linenumber = 1
            column = None

            stderr = strip_ansi_escape(run.stderr)
            stdout = strip_ansi_escape(run.stdout)

            for playbook_path in playbook_paths:
                filename = playbook_path
                if playbook_path in stderr:
                    if stderr:
                        details = stderr
                        if stdout:
                            details += "\n" + stdout
                    else:
                        details = stdout

                    match = _ansible_syntax_check_re.search(stderr)
                    if match:
                        message = match.groupdict()["title"]
                        # Ansible returns absolute paths
                        filename = match.groupdict()["filename"]
                        linenumber = int(match.groupdict()["line"])
                        column = int(match.groupdict()["column"])

                    match_error = AnsibleSyntaxCheckRule._get_match(
                        run=run,
                        message=message,
                        cmd=cmd,
                        filename=filename,
                        linenumber=linenumber,
                        column=column,
                        details=details,
                    )
                    result.append(match_error)
            # syntax check failed but we were not able to spot the playbook_path
            # that caused the error
            if not result:
                if len(playbook_paths) == 1:
                    match_error = AnsibleSyntaxCheckRule._get_match(
                        run=run, message=message, cmd=cmd, filename=playbook_paths[0]
                    )
                    result.append(match_error)
                else:
                    # We must call ourselves recursively to get to get more
                    # detailed errors.
                    result = []
                    for playbook_path in playbook_paths:
                        _logger.debug("Examining in isolation %s", playbook_path)
                        result.extend(
                            AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(
                                lintables=[
                                    Lintable(name=playbook_path, kind="playbook")
                                ]
                            )
                        )

        return result


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    def test_get_ansible_syntax_check_matches() -> None:
        """Validate parsing of ansible output."""
        lintable = Lintable(
            "examples/playbooks/conflicting_action.yml", kind="playbook"
        )
        # pylint: disable=protected-access
        result = AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches([lintable])
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
        result = AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches([lintable])
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
            "foo": "bar",
            "complex_variable": ":{;\t$()",
        }
        lintable = Lintable("examples/playbooks/extra_vars.yml", kind="playbook")

        # pylint: disable=protected-access
        result = AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches([lintable])

        assert not result
