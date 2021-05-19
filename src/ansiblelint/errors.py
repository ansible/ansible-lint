"""Exceptions and error representations."""
import functools
from typing import Any, Optional, Union

from ansiblelint._internal.rules import BaseRule, RuntimeErrorRule
from ansiblelint.file_utils import Lintable, normpath


@functools.total_ordering
class MatchError(ValueError):
    """Rule violation detected during linting.

    It can be raised as Exception but also just added to the list of found
    rules violations.

    Note that line argument is not considered when building hash of an
    instance.
    """

    # IMPORTANT: any additional comparison protocol methods must return
    # IMPORTANT: `NotImplemented` singleton to allow the check to use the
    # IMPORTANT: other object's fallbacks.
    # Ref: https://docs.python.org/3/reference/datamodel.html#object.__lt__

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        message: Optional[str] = None,
        # most linters report use (1,1) base, including yamllint and flake8
        # we should never report line 0 or column 0 in output.
        linenumber: int = 1,
        column: Optional[int] = None,
        details: str = "",
        filename: Optional[Union[str, Lintable]] = None,
        rule: BaseRule = RuntimeErrorRule(),
        tag: Optional[str] = None,  # optional fine-graded tag
    ) -> None:
        """Initialize a MatchError instance."""
        super().__init__(message)

        if rule.__class__ is RuntimeErrorRule and not message:
            raise TypeError(
                f'{self.__class__.__name__}() missing a '
                "required argument: one of 'message' or 'rule'",
            )

        self.message = message or getattr(rule, 'shortdesc', "")

        # Safety measture to ensure we do not endup with incorrect indexes
        if linenumber == 0:
            raise RuntimeError(
                "MatchError called incorrectly as line numbers start with 1"
            )
        if column == 0:
            raise RuntimeError(
                "MatchError called incorrectly as column numbers start with 1"
            )

        self.linenumber = linenumber
        self.column = column
        self.details = details
        self.filename = ""
        if filename:
            if isinstance(filename, Lintable):
                self.filename = normpath(str(filename.path))
            else:
                self.filename = normpath(filename)
        self.rule = rule
        self.ignored = False  # If set it will be displayed but not counted as failure
        # This can be used by rules that can report multiple errors type, so
        # we can still filter by them.
        self.tag = tag

    def __repr__(self) -> str:
        """Return a MatchError instance representation."""
        formatstr = u"[{0}] ({1}) matched {2}:{3} {4}"
        # note that `rule.id` can be int, str or even missing, as users
        # can defined their own custom rules.
        _id = getattr(self.rule, "id", "000")

        return formatstr.format(
            _id, self.message, self.filename, self.linenumber, self.details
        )

    @property
    def position(self) -> str:
        """Return error positioniong, with column number if available."""
        if self.column:
            return f"{self.linenumber}:{self.column}"
        return str(self.linenumber)

    @property
    def _hash_key(self) -> Any:
        # line attr is knowingly excluded, as dict is not hashable
        return (
            self.filename,
            self.linenumber,
            str(getattr(self.rule, 'id', 0)),
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

    def __hash__(self) -> int:
        """Return a hash value of the MatchError instance."""
        return hash(self._hash_key)

    def __eq__(self, other: object) -> bool:
        """Identify whether the other object represents the same rule match."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__hash__() == other.__hash__()
