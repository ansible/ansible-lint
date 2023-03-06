"""Module to deal with errors."""
from typing import TYPE_CHECKING, Any, Optional

from ansible_compat.constants import ANSIBLE_MISSING_RC, INVALID_PREREQUISITES_RC

if TYPE_CHECKING:
    from subprocess import CompletedProcess


class AnsibleCompatError(RuntimeError):
    """Generic error originating from ansible_compat library."""

    code = 1  # generic error

    def __init__(
        self, message: Optional[str] = None, proc: Optional[Any] = None
    ) -> None:
        """Construct generic library exception."""
        super().__init__(message)
        self.proc = proc


class AnsibleCommandError(RuntimeError):
    """Exception running an Ansible command."""

    def __init__(self, proc: "CompletedProcess[Any]") -> None:
        """Construct an exception given a completed process."""
        message = (
            f"Got {proc.returncode} exit code while running: {' '.join(proc.args)}"
        )
        super().__init__(message)
        self.proc = proc


class MissingAnsibleError(AnsibleCompatError):
    """Reports a missing or broken Ansible installation."""

    code = ANSIBLE_MISSING_RC

    def __init__(
        self, message: Optional[str] = None, proc: Optional[Any] = None
    ) -> None:
        """."""
        super().__init__(message)
        self.proc = proc


class InvalidPrerequisiteError(AnsibleCompatError):
    """Reports a missing requirement."""

    code = INVALID_PREREQUISITES_RC
