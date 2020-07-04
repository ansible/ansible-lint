"""Exceptions and error representations."""


class Match(ValueError):
    """Rule violation detected during linting.

    It can be raised as Exception but also just added to the list of found
    rules violations.
    """

    def __init__(self, message=None, linenumber=0, line=None, filename=None, rule=None) -> None:
        """Initialize a Match instance."""
        super().__init__(message)

        self.message = message or getattr(rule, 'shortdesc', "")
        self.linenumber = linenumber
        self.line = line
        self.filename = filename
        self.rule = rule

    def __repr__(self):
        """Return a Match instance representation."""
        formatstr = u"[{0}] ({1}) matched {2}:{3} {4}"
        # note that `rule.id` can be int, str or even missing, as users
        # can defined their own custom rules.
        _id = getattr(self.rule, "id", "000")

        return formatstr.format(_id, self.message,
                                self.filename, self.linenumber, self.line)
