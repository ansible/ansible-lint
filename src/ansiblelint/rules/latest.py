"""Implementation of latest rule."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class LatestRule(AnsibleLintRule):
    """Result of the command may vary on subsequent runs."""

    id = "latest"
    description = (
        "All version control checkouts must point to "
        "an explicit commit or tag, not just ``latest``"
    )
    severity = "MEDIUM"
    tags = ["idempotency"]
    version_added = "v6.5.2"

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None
    ) -> bool | str | MatchError:
        """Check if module args are safe."""
        if (
            task["action"]["__ansible_module__"] == "git"
            and task["action"].get("version", "HEAD") == "HEAD"
        ):
            return self.create_matcherror(tag="latest[git]", filename=file)
        if (
            task["action"]["__ansible_module__"] == "hg"
            and task["action"].get("revision", "default") == "default"
        ):
            return self.create_matcherror(tag="latest[hg]", filename=file)
        return False
