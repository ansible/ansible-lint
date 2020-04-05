"""Output formatters."""
import os
from pathlib import Path

try:
    from ansible import color
except ImportError:
    from ansible.utils import color


class BaseFormatter:
    """Formatter of ansible-lint output.

    Base class for output formatters.

    Args:
        base_dir (str|Path): reference directory against which display relative path.
        display_relative_path (bool): whether to show path as relatvie or absolute
    """

    def __init__(self, base_dir, display_relative_path):
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
        if colored:
            color.ANSIBLE_COLOR = True
            return formatstr.format(color.stringc(u"[{0}]".format(match.rule.id), 'bright red'),
                                    color.stringc(match.message, 'red'),
                                    color.stringc(self._format_path(match.filename), 'blue'),
                                    color.stringc(str(match.linenumber), 'cyan'),
                                    color.stringc(u"{0}".format(match.line), 'purple'))
        else:
            return formatstr.format(match.rule.id,
                                    match.message,
                                    match.filename,
                                    match.linenumber,
                                    match.line)


class QuietFormatter(BaseFormatter):

    def format(self, match, colored=False):
        formatstr = u"{0} {1}:{2}"
        if colored:
            color.ANSIBLE_COLOR = True
            return formatstr.format(color.stringc(u"[{0}]".format(match.rule.id), 'bright red'),
                                    color.stringc(self._format_path(match.filename), 'blue'),
                                    color.stringc(str(match.linenumber), 'cyan'))
        else:
            return formatstr.format(match.rule.id, self.f_ormat_path(match.filename),
                                    match.linenumber)


class ParseableFormatter(BaseFormatter):

    def format(self, match, colored=False):
        formatstr = u"{0}:{1}: [{2}] {3}"
        if colored:
            color.ANSIBLE_COLOR = True
            return formatstr.format(color.stringc(self._format_path(match.filename), 'blue'),
                                    color.stringc(str(match.linenumber), 'cyan'),
                                    color.stringc(u"E{0}".format(match.rule.id), 'bright red'),
                                    color.stringc(u"{0}".format(match.message), 'red'))
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
            color.ANSIBLE_COLOR = True
            filename = color.stringc(filename, 'blue')
            linenumber = color.stringc(linenumber, 'cyan')
            rule_id = color.stringc(rule_id, 'bright red')
            severity = color.stringc(severity, 'bright red')
            message = color.stringc(message, 'red')

        return formatstr.format(
            filename,
            linenumber,
            rule_id,
            severity,
            message,
        )
