"""Exceptions and error representations."""


class Match(object):
    """Rule violation detected during linting."""

    def __init__(self, linenumber, line, filename, rule, message=None) -> None:
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


class AnsibleLintInternalRule():
    """Internal error likely caused by parsing failures."""

    id = "999"
    shortdesc = "Parsing Error"
    description = "Ansible failed to file."


class MatchError(ValueError):
    """Exception that would end-up as linter rule match."""

    def __init__(self, message, rule=AnsibleLintInternalRule, filename="", linenumber=0, line=None):
        """Initialize a MatchError instance."""
        super().__init__(message)

        self.message = message
        self.linenumber = linenumber
        self.line = line
        self.filename = filename
        self.rule = rule

    def get_match(self) -> Match:
        """Return a Match instance."""
        return Match(self.linenumber, self.line, self.filename, self.rule, self.message)

    def __eq__(self, other):
        """Identify duplicate matches."""
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        """Perform hash of matches."""
        return hash((self.message, self.rule, self.filename, self.linenumber))
