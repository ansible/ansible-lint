"""Application."""
import logging
import os
from typing import TYPE_CHECKING, Any, List, Type

from ansiblelint import formatters
from ansiblelint.color import console
from ansiblelint.errors import MatchError

if TYPE_CHECKING:
    from argparse import Namespace


_logger = logging.getLogger(__package__)


class App:
    """App class represents an execution of the linter."""

    def __init__(self, options: "Namespace"):
        """Construct app run based on already loaded configuration."""
        options.skip_list = _sanitize_list_options(options.skip_list)
        options.warn_list = _sanitize_list_options(options.warn_list)

        self.options = options

        formatter_factory = choose_formatter_factory(options)
        self.formatter = formatter_factory(options.cwd, options.display_relative_path)

    def render_matches(self, matches: List[MatchError]) -> None:
        """Display given matches."""
        if isinstance(self.formatter, formatters.CodeclimateJSONFormatter):
            # If formatter CodeclimateJSONFormatter is chosen,
            # then print only the matches in JSON
            console.print(
                self.formatter.format_result(matches), markup=False, highlight=False
            )
            return None

        ignored_matches = [match for match in matches if match.ignored]
        fatal_matches = [match for match in matches if not match.ignored]
        # Displayed ignored matches first
        if ignored_matches:
            _logger.warning(
                "Listing %s violation(s) marked as ignored, likely already known",
                len(ignored_matches),
            )
            for match in ignored_matches:
                if match.ignored:
                    # highlight must be off or apostrophes may produce unexpected results
                    console.print(self.formatter.format(match), highlight=False)
        if fatal_matches:
            _logger.warning(
                "Listing %s violation(s) that are fatal", len(fatal_matches)
            )
            for match in fatal_matches:
                if not match.ignored:
                    console.print(self.formatter.format(match), highlight=False)

        # If run under GitHub Actions we also want to emit output recognized by it.
        if os.getenv('GITHUB_ACTIONS') == 'true' and os.getenv('GITHUB_WORKFLOW'):
            formatter = formatters.AnnotationsFormatter(self.options.cwd, True)
            for match in matches:
                console.print(formatter.format(match), markup=False, highlight=False)


def choose_formatter_factory(
    options_list: "Namespace",
) -> Type[formatters.BaseFormatter[Any]]:
    """Select an output formatter based on the incoming command line arguments."""
    r: Type[formatters.BaseFormatter[Any]] = formatters.Formatter
    if options_list.format == 'quiet':
        r = formatters.QuietFormatter
    elif options_list.parseable_severity:
        r = formatters.ParseableSeverityFormatter
    elif options_list.format == 'codeclimate':
        r = formatters.CodeclimateJSONFormatter
    elif options_list.parseable or options_list.format == 'pep8':
        r = formatters.ParseableFormatter
    return r


def _sanitize_list_options(tag_list: List[str]) -> List[str]:
    """Normalize list options."""
    # expand comma separated entries
    tags = set()
    for t in tag_list:
        tags.update(str(t).split(','))
    # remove duplicates, and return as sorted list
    return sorted(set(tags))
