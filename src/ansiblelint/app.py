"""Application."""
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any, List, Tuple, Type

from ansible_compat.runtime import Runtime

from ansiblelint import formatters
from ansiblelint._mockings import _perform_mockings
from ansiblelint.color import console, console_stderr, render_yaml
from ansiblelint.config import options as default_options
from ansiblelint.constants import SUCCESS_RC, VIOLATIONS_FOUND_RC
from ansiblelint.errors import MatchError

if TYPE_CHECKING:
    from argparse import Namespace
    from typing import Dict, Set  # pylint: disable=ungrouped-imports

    from ansiblelint._internal.rules import BaseRule
    from ansiblelint.file_utils import Lintable
    from ansiblelint.runner import LintResult


_logger = logging.getLogger(__package__)


@dataclass
class SummarizedResults:
    """The statistics about an ansible-lint run."""

    failures: int = 0
    warnings: int = 0
    fixed_failures: int = 0
    fixed_warnings: int = 0

    @property
    def fixed(self) -> int:
        """Get total fixed count."""
        return self.fixed_failures + self.fixed_warnings


class App:
    """App class represents an execution of the linter."""

    def __init__(self, options: "Namespace"):
        """Construct app run based on already loaded configuration."""
        options.skip_list = _sanitize_list_options(options.skip_list)
        options.warn_list = _sanitize_list_options(options.warn_list)

        self.options = options

        formatter_factory = choose_formatter_factory(options)
        self.formatter = formatter_factory(options.cwd, options.display_relative_path)

        self.runtime = Runtime(isolated=True)

    def render_matches(self, matches: List[MatchError]) -> None:
        """Display given matches (if they are not fixed)."""
        matches = [match for match in matches if not match.fixed]

        if isinstance(
            self.formatter,
            (formatters.CodeclimateJSONFormatter, formatters.SarifFormatter),
        ):
            # If formatter CodeclimateJSONFormatter or SarifFormatter is chosen,
            # then print only the matches in JSON
            console.print(
                self.formatter.format_result(matches), markup=False, highlight=False
            )
            return

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

    def count_results(self, matches: List[MatchError]) -> SummarizedResults:
        """Count failures and warnings in matches."""
        failures = 0
        warnings = 0
        fixed_failures = 0
        fixed_warnings = 0
        for match in matches:
            if {match.rule.id, *match.rule.tags}.isdisjoint(self.options.warn_list):
                if match.fixed:
                    fixed_failures += 1
                else:
                    failures += 1
            else:
                if match.fixed:
                    fixed_warnings += 1
                else:
                    warnings += 1
        return SummarizedResults(failures, warnings, fixed_failures, fixed_warnings)

    @staticmethod
    def count_lintables(files: "Set[Lintable]") -> Tuple[int, int]:
        """Count total and modified files."""
        files_count = len(files)
        changed_files_count = len([file for file in files if file.updated])
        return files_count, changed_files_count

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

        summary = self.count_results(result.matches)
        files_count, changed_files_count = self.count_lintables(result.files)

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
# .config/ansible-lint.yml
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

        if self.options.write_list and "yaml" in self.options.skip_list:
            _logger.warning(
                "You specified '--write', but no files can be modified "
                "because 'yaml' is in 'skip_list'."
            )

        if (result.matches or changed_files_count) and not self.options.quiet:
            console_stderr.print(render_yaml(msg))
            self.report_summary(summary, changed_files_count, files_count)

        if mark_as_success or not summary.failures:
            return SUCCESS_RC
        return VIOLATIONS_FOUND_RC

    @staticmethod
    def report_summary(
        summary: SummarizedResults, changed_files_count: int, files_count: int
    ) -> None:
        """Report match and file counts."""
        if changed_files_count:
            console_stderr.print(f"Modified {changed_files_count} files.")

        msg = "Finished with "
        msg += f"{summary.failures} failure(s), {summary.warnings} warning(s)"
        if summary.fixed:
            msg += f", and fixed {summary.fixed} issue(s)"
        msg += f" on {files_count} files."

        console_stderr.print(msg)


def choose_formatter_factory(
    options_list: "Namespace",
) -> Type[formatters.BaseFormatter[Any]]:
    """Select an output formatter based on the incoming command line arguments."""
    r: Type[formatters.BaseFormatter[Any]] = formatters.Formatter
    if options_list.format == "quiet":
        r = formatters.QuietFormatter
    elif options_list.format in ("json", "codeclimate"):
        r = formatters.CodeclimateJSONFormatter
    elif options_list.format == "sarif":
        r = formatters.SarifFormatter
    elif options_list.parseable or options_list.format == "pep8":
        r = formatters.ParseableFormatter
    return r


def _sanitize_list_options(tag_list: List[str]) -> List[str]:
    """Normalize list options."""
    # expand comma separated entries
    tags = set()
    for tag in tag_list:
        tags.update(str(tag).split(","))
    # remove duplicates, and return as sorted list
    return sorted(set(tags))


@lru_cache(maxsize=1)
def get_app(offline: bool = False) -> App:
    """Return the application instance."""
    app = App(options=default_options)
    # Make linter use the cache dir from compat
    default_options.cache_dir = app.runtime.cache_dir

    app.runtime.prepare_environment(offline=offline)
    _perform_mockings()
    return app
