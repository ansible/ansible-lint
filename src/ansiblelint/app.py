"""Application."""
import logging
import os
from typing import TYPE_CHECKING, Any, List, Tuple, Type

from ansiblelint import formatters
from ansiblelint.color import console, console_stderr, render_yaml
from ansiblelint.errors import MatchError

if TYPE_CHECKING:
    from argparse import Namespace
    from typing import Dict  # pylint: disable=ungrouped-imports

    from ansiblelint._internal.rules import BaseRule
    from ansiblelint.runner import LintResult


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
        if os.getenv("GITHUB_ACTIONS") == "true" and os.getenv("GITHUB_WORKFLOW"):
            formatter = formatters.AnnotationsFormatter(self.options.cwd, True)
            for match in matches:
                console.print(formatter.format(match), markup=False, highlight=False)

    def count_results(self, matches: List[MatchError]) -> Tuple[int, int]:
        """Count failures and warnings in matches."""
        failures = 0
        warnings = 0
        for match in matches:
            if {match.rule.id, *match.rule.tags}.isdisjoint(self.options.warn_list):
                failures += 1
            else:
                warnings += 1
        return failures, warnings

    @staticmethod
    def _get_matched_skippable_rules(
        matches: List[MatchError],
    ) -> "Dict[str, BaseRule]":
        """Extract the list of matched rules, if skippable, from the list of matches."""
        matches_unignored = [match for match in matches if not match.ignored]
        matched_rules = {match.rule.id: match.rule for match in matches_unignored}
        # remove unskippable rules from the list
        for rule_id in list(matched_rules.keys()):
            if "unskippable" in matched_rules[rule_id].tags:
                matched_rules.pop(rule_id)
        return matched_rules

    def report_outcome(
        self, result: "LintResult", mark_as_success: bool = False
    ) -> int:
        """Display information about how to skip found rules.

        Returns exit code, 2 if errors were found, 0 when only warnings were found.
        """
        msg = ""

        failures, warnings = self.count_results(result.matches)

        matched_rules = self._get_matched_skippable_rules(result.matches)

        entries = []
        for key in sorted(matched_rules.keys()):
            if {key, *matched_rules[key].tags}.isdisjoint(self.options.warn_list):
                entries.append(f"  - {key}  # {matched_rules[key].shortdesc}\n")
        for match in result.matches:
            if "experimental" in match.rule.tags:
                entries.append("  - experimental  # all rules tagged as experimental\n")
                break
        if entries and not self.options.quiet:
            console_stderr.print(
                "You can skip specific rules or tags by adding them to your "
                "configuration file:"
            )
            msg += """\
# .ansible-lint
warn_list:  # or 'skip_list' to silence them completely
"""
            msg += "".join(sorted(entries))

        # Do not deprecate the old tags just yet. Why? Because it is not currently feasible
        # to migrate old tags to new tags. There are a lot of things out there that still
        # use ansible-lint 4 (for example, Ansible Galaxy and Automation Hub imports). If we
        # replace the old tags, those tools will report warnings. If we do not replace them,
        # ansible-lint 5 will report warnings.
        #
        # We can do the deprecation once the ecosystem caught up at least a bit.
        # for k, v in used_old_tags.items():
        #     _logger.warning(
        #         "Replaced deprecated tag '%s' with '%s' but it will become an "
        #         "error in the future.",
        #         k,
        #         v,
        #     )

        if result.matches and not self.options.quiet:
            console_stderr.print(render_yaml(msg))
            console_stderr.print(
                f"Finished with {failures} failure(s), {warnings} warning(s) "
                f"on {len(result.files)} files."
            )

        if mark_as_success or not failures:
            return 0
        return 2


def choose_formatter_factory(
    options_list: "Namespace",
) -> Type[formatters.BaseFormatter[Any]]:
    """Select an output formatter based on the incoming command line arguments."""
    r: Type[formatters.BaseFormatter[Any]] = formatters.Formatter
    if options_list.format == "quiet":
        r = formatters.QuietFormatter
    elif options_list.parseable_severity:
        r = formatters.ParseableSeverityFormatter
    elif options_list.format == "codeclimate":
        r = formatters.CodeclimateJSONFormatter
    elif options_list.parseable or options_list.format == "pep8":
        r = formatters.ParseableFormatter
    return r


def _sanitize_list_options(tag_list: List[str]) -> List[str]:
    """Normalize list options."""
    # expand comma separated entries
    tags = set()
    for t in tag_list:
        tags.update(str(t).split(","))
    # remove duplicates, and return as sorted list
    return sorted(set(tags))
