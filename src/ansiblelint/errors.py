"""Exceptions and error representations."""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ansiblelint._internal.rules import BaseRule, RuntimeErrorRule
from ansiblelint.file_utils import Lintable

if TYPE_CHECKING:
    from ansiblelint.utils import Task


class LintWarning(Warning):
    """Used by linter."""


@dataclass
class WarnSource:
    """Container for warning information, so we can later create a MatchError from it."""

    filename: Lintable
    lineno: int
    tag: str
    message: str | None = None


@dataclass(frozen=True)
class RuleMatchTransformMeta:
    """Additional metadata about a match error to be used during transformation."""


# pylint: disable=too-many-instance-attributes
@dataclass(unsafe_hash=True)
@functools.total_ordering
class MatchError(ValueError):
    """Rule violation detected during linting.

    It can be raised as Exception but also just added to the list of found
    rules violations.

    Note that line argument is not considered when building hash of an
    instance.
    """

    # order matters for these:
    message: str = field(init=True, repr=False, default="")
    lintable: Lintable = field(init=True, repr=False, default=Lintable(name=""))
    filename: str = field(init=True, repr=False, default="")

    tag: str = field(init=True, repr=False, default="")
    lineno: int = 1
    details: str = ""
    column: int | None = None
    # rule is not included in hash because we might have different instances
    # of the same rule, but we use the 'tag' to identify the rule.
    rule: BaseRule = field(hash=False, default=RuntimeErrorRule())
    ignored: bool = False
    fixed: bool = False  # True when a transform has resolved this MatchError
    transform_meta: RuleMatchTransformMeta | None = None

    def __post_init__(self) -> None:
        """Can be use by rules that can report multiple errors type, so we can still filter by them."""
        if not self.lintable and self.filename:
            self.lintable = Lintable(self.filename)
        elif self.lintable and not self.filename:
            self.filename = self.lintable.name

        # We want to catch accidental MatchError() which contains no useful
        # information. When no arguments are passed, the '_message' field is
        # set to 'property', only if passed it becomes a string.
        if self.rule.__class__ is RuntimeErrorRule:
            # so instance was created without a rule
            if not self.message:
                msg = f"{self.__class__.__name__}() missing a required argument: one of 'message' or 'rule'"
                raise TypeError(msg)
            if not isinstance(self.tag, str):
                msg = "MatchErrors must be created with either rule or tag specified."
                raise TypeError(msg)
        if not self.message:
            self.message = self.rule.shortdesc

        self.match_type: str | None = None
        # for task matches, save the normalized task object (useful for transforms)
        self.task: Task | None = None
        # path to the problem area, like: [0,"pre_tasks",3] for [0].pre_tasks[3]
        self.yaml_path: list[int | str] = []

        if not self.tag:
            self.tag = self.rule.id

        # Safety measure to ensure we do not end-up with incorrect indexes
        if self.lineno == 0:  # pragma: no cover
            msg = "MatchError called incorrectly as line numbers start with 1"
            raise RuntimeError(msg)
        if self.column == 0:  # pragma: no cover
            msg = "MatchError called incorrectly as column numbers start with 1"
            raise RuntimeError(msg)

        self.lineno += self.lintable.line_offset

        # We make the lintable aware that we found a match inside it, as this
        # can be used to skip running other rules that do require current one
        # to pass.
        self.lintable.matches.append(self)

    @functools.cached_property
    def level(self) -> str:
        """Return the level of the rule: error, warning or notice."""
        if not self.ignored and {self.tag, self.rule.id, *self.rule.tags}.isdisjoint(
            self.rule.options.warn_list,
        ):
            return "error"
        return "warning"

    def __repr__(self) -> str:
        """Return a MatchError instance representation."""
        formatstr = "[{0}] ({1}) matched {2}:{3} {4}"
        # note that `rule.id` can be int, str or even missing, as users
        # can defined their own custom rules.
        _id = getattr(self.rule, "id", "000")

        return formatstr.format(
            _id,
            self.message,
            self.filename,
            self.lineno,
            self.details,
        )

    def __str__(self) -> str:
        """Return a MatchError instance string representation."""
        return self.__repr__()

    @property
    def position(self) -> str:
        """Return error positioning, with column number if available."""
        if self.column:
            return f"{self.lineno}:{self.column}"
        return str(self.lineno)

    @property
    def _hash_key(self) -> Any:
        # line attr is knowingly excluded, as dict is not hashable
        return (
            self.filename,
            self.lineno,
            str(getattr(self.rule, "id", 0)),
            self.message,
            self.details,
            # -1 is used here to force errors with no column to sort before
            # all other errors.
            -1 if self.column is None else self.column,
        )

    def __lt__(self, other: object) -> bool:
        """Return whether the current object is less than the other."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return bool(self._hash_key < other._hash_key)

    def __eq__(self, other: object) -> bool:
        """Identify whether the other object represents the same rule match."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__hash__() == other.__hash__()
