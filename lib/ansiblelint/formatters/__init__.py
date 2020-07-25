"""Output formatters."""
import os
from pathlib import Path

from ansiblelint.color import Color, colorize


class BaseFormatter:
    """Formatter of ansible-lint output.

    Base class for output formatters.

    Args:
        base_dir (str|Path): reference directory against which display relative path.
        display_relative_path (bool): whether to show path as relative or absolute
    """

    def __init__(self, base_dir, display_relative_path):
        """Initialize a BaseFormatter instance."""
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)
        if base_dir:  # can be None
            base_dir = base_dir.absolute()

        # Required 'cause os.path.relpath() does not accept Path before 3.6
        if isinstance(base_dir, Path):
            base_dir = str(base_dir)  # Drop when Python 3.5 is no longer supported

        self._base_dir = base_dir if display_relative_path else None

    def _format_path(self, path):
        # Required 'cause os.path.relpath() does not accept Path before 3.6
        if isinstance(path, Path):
            path = str(path)  # Drop when Python 3.5 is no longer supported

        if not self._base_dir:
            return path
        # Use os.path.relpath 'cause Path.relative_to() misbehaves
        return os.path.relpath(path, start=self._base_dir)


class Formatter(BaseFormatter):

    def format(self, match, colored=False):
        formatstr = u"{0} {1}\n{2}:{3}\n{4}\n"
        _id = getattr(match.rule, 'id', '000')
        if colored:
            return formatstr.format(colorize(u"[{0}]".format(_id), Color.error_code),
                                    colorize(match.message, Color.error_title),
                                    colorize(self._format_path(match.filename), Color.filename),
                                    colorize(str(match.linenumber), Color.linenumber),
                                    colorize(u"{0}".format(match.details), Color.line))
        else:
            return formatstr.format(_id,
                                    match.message,
                                    match.filename,
                                    match.linenumber,
                                    match.details)


class QuietFormatter(BaseFormatter):

    def format(self, match, colored=False):
        formatstr = u"{0} {1}:{2}"
        if colored:
            return formatstr.format(colorize(u"[{0}]".format(match.rule.id), Color.error_code),
                                    colorize(self._format_path(match.filename), Color.filename),
                                    colorize(str(match.linenumber), Color.linenumber))
        else:
            return formatstr.format(match.rule.id, self.format_path(match.filename),
                                    match.linenumber)


class ParseableFormatter(BaseFormatter):

    def format(self, match, colored=False):
        formatstr = u"{0}:{1}: [{2}] {3}"
        if colored:
            return formatstr.format(colorize(self._format_path(match.filename), Color.filename),
                                    colorize(str(match.linenumber), Color.linenumber),
                                    colorize(u"E{0}".format(match.rule.id), Color.error_code),
                                    colorize(u"{0}".format(match.message), Color.error_title))
        else:
            return formatstr.format(self._format_path(match.filename),
                                    match.linenumber,
                                    "E" + match.rule.id,
                                    match.message)


class ParseableSeverityFormatter(BaseFormatter):

    def format(self, match, colored=False):
        formatstr = u"{0}:{1}: [{2}] [{3}] {4}"

        filename = self._format_path(match.filename)
        linenumber = str(match.linenumber)
        rule_id = u"E{0}".format(match.rule.id)
        severity = match.rule.severity
        message = str(match.message)

        if colored:
            filename = colorize(filename, Color.filename)
            linenumber = colorize(linenumber, Color.linenumber)
            rule_id = colorize(rule_id, Color.error_code)
            severity = colorize(severity, Color.error_code)
            message = colorize(message, Color.error_title)

        return formatstr.format(
            filename,
            linenumber,
            rule_id,
            severity,
            message,
        )
