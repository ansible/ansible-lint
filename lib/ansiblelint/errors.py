"""Exceptions and error representations."""
import functools
from ansiblelint.file_utils import normpath


@functools.total_ordering
class MatchError(ValueError):
    """Rule violation detected during linting.

    It can be raised as Exception but also just added to the list of found
    rules violations.
    """

    def __init__(self, message=None, linenumber=0, line=None, filename=None, rule=None) -> None:
        """Initialize a MatchError instance."""
        super().__init__(message)

        if not (message or rule):
            self.linenumber = 0
            raise RuntimeError("Calling MatchError requires either a message or a rule.")

        self.message = message or getattr(rule, 'shortdesc', "")
        self.linenumber = linenumber
        self.line = line
        self.filename = normpath(filename) if filename else None
        self.rule = rule

    def __repr__(self):
        """Return a MatchError instance representation."""
        formatstr = u"[{0}] ({1}) matched {2}:{3} {4}"
        # note that `rule.id` can be int, str or even missing, as users
        # can defined their own custom rules.
        _id = getattr(self.rule, "id", "000")

        return formatstr.format(_id, self.message,
                                self.filename, self.linenumber, self.line)

    @property
    def _hash_key(self):
        return self.filename, self.linenumber, self.message, getattr(self.rule, 'id', 0)

    def __lt__(self, other):
        """Enable sorting of MatchError instances."""
        return self._hash_key < other._hash_key

    def __hash__(self):
        """Perform hash of matches."""
        return hash(self._hash_key)

    def __eq__(self, other):
        """Identify duplicate matches."""
        return self.__hash__() == other.__hash__()
