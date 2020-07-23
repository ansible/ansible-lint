"""Exceptions and error representations."""
import functools

from ansiblelint.file_utils import normpath


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

    def __init__(
            self,
            message=None,
            linenumber=0,
            details: str = "",
            filename=None,
            rule=None) -> None:
        """Initialize a MatchError instance."""
        super().__init__(message)

        if not (message or rule):
            raise TypeError(
                f'{self.__class__.__name__}() missing a '
                "required argument: one of 'message' or 'rule'",
            )

        self.message = message or getattr(rule, 'shortdesc', "")
        self.linenumber = linenumber
        self.details = details
        self.filename = normpath(filename) if filename else None
        self.rule = rule

    def __repr__(self):
        """Return a MatchError instance representation."""
        formatstr = u"[{0}] ({1}) matched {2}:{3} {4}"
        # note that `rule.id` can be int, str or even missing, as users
        # can defined their own custom rules.
        _id = getattr(self.rule, "id", "000")

        return formatstr.format(_id, self.message,
                                self.filename, self.linenumber, self.details)

    @property
    def _hash_key(self):
        # line attr is knowingly excluded, as dict is not hashable
        return (
            self.filename,
            self.linenumber,
            str(getattr(self.rule, 'id', 0)),
            self.message,
            self.details,
        )

    def __lt__(self, other):
        """Return whether the current object is less than the other."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._hash_key < other._hash_key

    def __hash__(self):
        """Return a hash value of the MatchError instance."""
        return hash(self._hash_key)

    def __eq__(self, other):
        """Identify whether the other object represents the same rule match."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__hash__() == other.__hash__()
