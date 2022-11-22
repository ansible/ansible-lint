"""Application."""
from __future__ import annotations

import itertools
import logging
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from ansible_compat.runtime import Runtime
from rich.markup import escape
from rich.table import Table

from ansiblelint import formatters
from ansiblelint._mockings import _perform_mockings
from ansiblelint.color import console, console_stderr, render_yaml
from ansiblelint.config import PROFILES, get_version_warning
from ansiblelint.config import options as default_options
from ansiblelint.constants import RULE_DOC_URL, SUCCESS_RC, VIOLATIONS_FOUND_RC
from ansiblelint.errors import MatchError
from ansiblelint.stats import SummarizedResults, TagStats

if TYPE_CHECKING:
    from argparse import Namespace
    from typing import Dict, Set  # pylint: disable=ungrouped-imports

    from ansiblelint._internal.rules import BaseRule
    from ansiblelint.file_utils import Lintable
    from ansiblelint.runner import LintResult


_logger = logging.getLogger(__package__)


class App:
    """App class represents an execution of the linter."""

    def __init__(self, options: Namespace):
        """Construct app run based on already loaded configuration."""
        options.skip_list = _sanitize_list_options(options.skip_list)
        options.warn_list = _sanitize_list_options(options.warn_list)

        self.options = options

        formatter_factory = choose_formatter_factory(options)
        self.formatter = formatter_factory(options.cwd, options.display_relative_path)

        self.runtime = Runtime(isolated=True)

    def render_matches(self, matches: list[MatchError]) -> None:
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
            for match in itertools.chain(fatal_matches, ignored_matches):
                console.print(formatter.format(match), markup=False, highlight=False)

    def count_results(self, matches: list[MatchError]) -> SummarizedResults:
        """Count failures and warnings in matches."""
        result = SummarizedResults()

        for match in matches:
            # tag can include a sub-rule id: `yaml[document-start]`
            # rule.id is the generic rule id: `yaml`
            # *rule.tags is the list of the rule's tags (categories): `style`
            if match.tag not in result.tag_stats:
                result.tag_stats[match.tag] = TagStats(
                    tag=match.tag, count=1, associated_tags=match.rule.tags
                )
            else:
                result.tag_stats[match.tag].count += 1

            if {match.tag, match.rule.id, *match.rule.tags}.isdisjoint(
                self.options.warn_list
            ):
                # not in warn_list
                if match.fixed:
                    result.fixed_failures += 1
                else:
                    result.failures += 1
            else:
                result.tag_stats[match.tag].warning = True
                if match.fixed:
                    result.fixed_warnings += 1
                else:
                    result.warnings += 1
        return result

    @staticmethod
    def count_lintables(files: set[Lintable]) -> tuple[int, int]:
        """Count total and modified files."""
        files_count = len(files)
        changed_files_count = len([file for file in files if file.updated])
        return files_count, changed_files_count

    @staticmethod
    def _get_matched_skippable_rules(
        matches: list[MatchError],
    ) -> dict[str, BaseRule]:
        """Extract the list of matched rules, if skippable, from the list of matches."""
        matches_unignored = [match for match in matches if not match.ignored]
        # match.tag is more specialized than match.rule.id
        matched_rules = {
            match.tag or match.rule.id: match.rule for match in matches_unignored
        }
        # remove unskippable rules from the list
        for rule_id in list(matched_rules.keys()):
            if "unskippable" in matched_rules[rule_id].tags:
                matched_rules.pop(rule_id)
        return matched_rules

    def report_outcome(self, result: LintResult, mark_as_success: bool = False) -> int:
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

        if mark_as_success and summary.failures and not self.options.progressive:
            mark_as_success = False

        if not self.options.quiet:
            console_stderr.print(render_yaml(msg))
            self.report_summary(
                summary, changed_files_count, files_count, is_success=mark_as_success
            )

        return SUCCESS_RC if mark_as_success else VIOLATIONS_FOUND_RC

    def report_summary(  # pylint: disable=too-many-branches,too-many-locals
        self,
        summary: SummarizedResults,
        changed_files_count: int,
        files_count: int,
        is_success: bool,
    ) -> None:
        """Report match and file counts."""
        # sort the stats by profiles
        idx = 0
        rule_order = {}

        for profile, profile_config in PROFILES.items():
            for rule in profile_config["rules"]:
                # print(profile, rule)
                rule_order[rule] = (idx, profile)
                idx += 1
        _logger.debug("Determined rule-profile order: %s", rule_order)
        failed_profiles = set()
        for tag, tag_stats in summary.tag_stats.items():
            if tag in rule_order:
                tag_stats.order, tag_stats.profile = rule_order.get(tag, (idx, ""))
            elif "[" in tag:
                tag_stats.order, tag_stats.profile = rule_order.get(
                    tag.split("[")[0], (idx, "")
                )
            if tag_stats.profile:
                failed_profiles.add(tag_stats.profile)
        summary.sort()

        if changed_files_count:
            console_stderr.print(f"Modified {changed_files_count} files.")

        # determine which profile passed
        summary.passed_profile = ""
        passed_profile_count = 0
        for profile in PROFILES.keys():
            if profile in failed_profiles:
                break
            if profile != summary.passed_profile:
                summary.passed_profile = profile
                passed_profile_count += 1

        stars = ""
        if summary.tag_stats:
            table = Table(
                title="Rule Violation Summary",
                collapse_padding=True,
                box=None,
                show_lines=False,
            )
            table.add_column("count", justify="right")
            table.add_column("tag")
            table.add_column("profile")
            table.add_column("rule associated tags")
            for tag, stats in summary.tag_stats.items():
                table.add_row(
                    str(stats.count),
                    f"[link={RULE_DOC_URL}{ tag.split('[')[0] }]{escape(tag)}[/link]",
                    stats.profile,
                    f"{', '.join(stats.associated_tags)}{' (warning)' if stats.warning else ''}",
                    style="yellow" if stats.warning else "red",
                )
            # rate stars for the top 5 profiles (min would not get
            rating = 5 - (len(PROFILES.keys()) - passed_profile_count)
            if 0 < rating < 6:
                stars = f", {rating}/5 star rating"

            console_stderr.print(table)
            console_stderr.print()

        if is_success:
            msg = "[green]Passed[/] with "
        else:
            msg = "[red][bold]Failed[/][/] after "

        if summary.passed_profile:
            msg += f"[bold]{summary.passed_profile}[/] profile"
        if stars:
            msg += stars

        msg += f": {summary.failures} failure(s), {summary.warnings} warning(s)"
        if summary.fixed:
            msg += f", and fixed {summary.fixed} issue(s)"
        msg += f" on {files_count} files."

        if not self.options.offline:
            version_warning = get_version_warning()
            if version_warning:
                msg += f"\n{version_warning}"

        console_stderr.print(msg)


def choose_formatter_factory(
    options_list: Namespace,
) -> type[formatters.BaseFormatter[Any]]:
    """Select an output formatter based on the incoming command line arguments."""
    r: type[formatters.BaseFormatter[Any]] = formatters.Formatter
    if options_list.format == "quiet":
        r = formatters.QuietFormatter
    elif options_list.format in ("json", "codeclimate"):
        r = formatters.CodeclimateJSONFormatter
    elif options_list.format == "sarif":
        r = formatters.SarifFormatter
    elif options_list.parseable or options_list.format == "pep8":
        r = formatters.ParseableFormatter
    return r


def _sanitize_list_options(tag_list: list[str]) -> list[str]:
    """Normalize list options."""
    # expand comma separated entries
    tags = set()
    for tag in tag_list:
        tags.update(str(tag).split(","))
    # remove duplicates, and return as sorted list
    return sorted(set(tags))


@lru_cache
def get_app() -> App:
    """Return the application instance, caching the return value."""
    offline = default_options.offline
    app = App(options=default_options)
    # Make linter use the cache dir from compat
    default_options.cache_dir = app.runtime.cache_dir

    role_name_check = 0
    if "role-name" in app.options.warn_list:
        role_name_check = 1
    elif "role-name" in app.options.skip_list:
        role_name_check = 2

    # mocking must happen before prepare_environment or galaxy install might
    # fail.
    _perform_mockings()
    app.runtime.prepare_environment(
        install_local=True, offline=offline, role_name_check=role_name_check
    )

    return app
