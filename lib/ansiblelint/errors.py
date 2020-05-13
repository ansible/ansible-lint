"""Exceptions and error representations."""


class Match(object):
    """Rule violation detected during linting."""

    def __init__(self, linenumber, line, filename, rule, message=None):
        """Initialize a Match instance."""
        self.linenumber = linenumber
        self.line = line
        self.filename = filename
        self.rule = rule
        self.message = message or rule.shortdesc

    def __repr__(self):
        """Return a Match instance representation."""
        formatstr = u"[{0}] ({1}) matched {2}:{3} {4}"
        return formatstr.format(self.rule.id, self.message,
                                self.filename, self.linenumber, self.line)
