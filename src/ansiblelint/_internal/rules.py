"""Internally used rule classes."""

from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ansiblelint.constants import RULE_DOC_URL

if TYPE_CHECKING:
    from ansiblelint.config import Options
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.rules import RulesCollection
    from ansiblelint.utils import Task

_logger = logging.getLogger(__name__)
LOAD_FAILURE_MD = """\
# load-failure

"Linter failed to process a file, possible invalid file. Possible reasons:

* contains unsupported encoding (only UTF-8 is supported)
* not an Ansible file
* it contains some unsupported custom YAML objects (`!!` prefix)
* it was not able to decrypt an inline `!vault` block.

This violation **is not** skippable, so it cannot be added to the `warn_list`
or the `skip_list`. If a vault decryption issue cannot be avoided, the
offending file can be added to `exclude_paths` configuration.
"""


# Derived rules are likely to want to access class members, so:
# pylint: disable=unused-argument
class BaseRule:
    """Root class used by Rules."""

    id: str = ""
    tags: list[str] = []
    description: str = ""
    version_added: str = ""
    severity: str = ""
    link: str = ""
    has_dynamic_tags: bool = False
    needs_raw_task: bool = False
    # Used to mark rules that we will never unload (internal ones)
    unloadable: bool = False
    # We use _order to sort rules and to ensure that some run before others,
    # _order 0 for internal rules
    # _order 1 for rules that check that data can be loaded
    # _order 5 implicit for normal rules
    _order: int = 5
    _help: str | None = None
    # Added when a rule is registered into a collection, gives access to options
    _collection: RulesCollection | None = None

    @property
    def help(self) -> str:
        """Return a help markdown string for the rule."""
        if self._help is None:
            self._help = ""
            md_file = (
                Path(inspect.getfile(self.__class__)).parent
                / f"{self.id.replace('-', '_')}.md"
            )
            if md_file.exists():
                self._help = md_file.read_text(encoding="utf-8")
        return self._help

    @property
    def url(self) -> str:
        """Return rule documentation url."""
        url = self.link
        if not url:  # pragma: no cover
            url = RULE_DOC_URL
            if self.id:
                url += self.id + "/"
        return url

    @property
    def shortdesc(self) -> str:
        """Return the short description of the rule, basically the docstring."""
        return self.__doc__ or ""

    def getmatches(self, file: Lintable) -> list[MatchError]:
        """Return all matches while ignoring exceptions."""
        matches = []
        if not file.path.is_dir():
            for method in [self.matchlines, self.matchtasks, self.matchyaml]:
                try:
                    matches.extend(method(file))
                except Exception as exc:  # pylint: disable=broad-except # noqa: BLE001
                    _logger.warning(
                        "Ignored exception from %s.%s while processing %s: %s",
                        self.__class__.__name__,
                        method.__name__,
                        str(file),
                        exc,
                    )
                    _logger.debug("Ignored exception details", exc_info=True)
        else:
            matches.extend(self.matchdir(file))
        return matches

    def matchlines(self, file: Lintable) -> list[MatchError]:
        """Return matches found for a specific line."""
        return []

    def matchtask(
        self,
        task: Task,
        file: Lintable | None = None,
    ) -> bool | str | MatchError | list[MatchError]:
        """Confirm if current rule is matching a specific task.

        If ``needs_raw_task`` (a class level attribute) is ``True``, then
        the original task (before normalization) will be made available under
        ``task["__raw_task__"]``.
        """
        return False

    def matchtasks(self, file: Lintable) -> list[MatchError]:
        """Return matches for a tasks file."""
        return []

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches found for a specific YAML text."""
        return []

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Return matches found for a specific playbook."""
        return []

    def matchdir(self, lintable: Lintable) -> list[MatchError]:
        """Return matches for lintable folders."""
        return []

    def verbose(self) -> str:
        """Return a verbose representation of the rule."""
        return self.id + ": " + self.shortdesc + "\n  " + self.description

    def match(self, line: str) -> bool | str:
        """Confirm if current rule matches the given string."""
        return False

    def __lt__(self, other: BaseRule) -> bool:
        """Enable us to sort rules by their id."""
        return (self._order, self.id) < (other._order, other.id)

    def __repr__(self) -> str:
        """Return a AnsibleLintRule instance representation."""
        return self.id + ": " + self.shortdesc

    @classmethod
    def ids(cls) -> dict[str, str]:
        """Return a dictionary ids and their messages.

        This is used by the ``--list-tags`` option to ansible-lint.
        """
        return getattr(cls, "_ids", {cls.id: cls.shortdesc})

    @property
    def rule_config(self) -> dict[str, Any]:
        """Retrieve rule specific configuration."""
        rule_config = self.options.rules.get(self.id, {})
        if not isinstance(rule_config, dict):  # pragma: no branch
            msg = f"Invalid rule config for {self.id}: {rule_config}"
            raise RuntimeError(msg)  # noqa: TRY004
        return rule_config

    @property
    def options(self) -> Options:
        """Used to access linter configuration."""
        if self._collection is None:
            msg = f"A rule ({self.id}) that is not part of a collection cannot access its configuration."
            _logger.warning(msg)
            raise RuntimeError(msg)
        return self._collection.options


# pylint: enable=unused-argument


class RuntimeErrorRule(BaseRule):
    """Unexpected internal error."""

    id = "internal-error"
    shortdesc = "Unexpected internal error"
    severity = "VERY_HIGH"
    tags = ["core"]
    version_added = "v5.0.0"
    _order = 0
    unloadable = True


class AnsibleParserErrorRule(BaseRule):
    """AnsibleParserError."""

    id = "parser-error"
    description = "Ansible parser fails; this usually indicates an invalid file."
    severity = "VERY_HIGH"
    tags = ["core"]
    version_added = "v5.0.0"
    _order = 0
    unloadable = True


class LoadingFailureRule(BaseRule):
    """Failed to load or parse file."""

    id = "load-failure"
    description = "Linter failed to process a file, possible invalid file."
    severity = "VERY_HIGH"
    tags = ["core", "unskippable"]
    version_added = "v4.3.0"
    _help = LOAD_FAILURE_MD
    _order = 0
    _ids = {
        "load-failure[not-found]": "File not found",
    }
    unloadable = True


class WarningRule(BaseRule):
    """Other warnings detected during run."""

    id = "warning"
    severity = "LOW"
    # should remain experimental as that would keep it warning only
    tags = ["core", "experimental"]
    version_added = "v6.8.0"
    _order = 0
    unloadable = True
