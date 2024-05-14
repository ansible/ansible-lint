"""Application."""

from __future__ import annotations

import copy
import itertools
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ansible_compat.runtime import Runtime
from rich.markup import escape
from rich.table import Table

from ansiblelint import formatters
from ansiblelint._mockings import _perform_mockings
from ansiblelint.color import console, console_stderr, render_yaml
from ansiblelint.config import PROFILES, Options, get_version_warning
from ansiblelint.config import options as default_options
from ansiblelint.constants import RC, RULE_DOC_URL
from ansiblelint.loaders import IGNORE_FILE
from ansiblelint.requirements import Reqs
from ansiblelint.stats import SummarizedResults, TagStats

if TYPE_CHECKING:
    from ansiblelint._internal.rules import BaseRule
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable
    from ansiblelint.runner import LintResult


_logger = logging.getLogger(__package__)
_CACHED_APP = None


class App:
    """App class represents an execution of the linter."""

    def __init__(self, options: Options):
        """Construct app run based on already loaded configuration."""
        options.skip_list = _sanitize_list_options(options.skip_list)
        options.warn_list = _sanitize_list_options(options.warn_list)

        self.options = options

        formatter_factory = choose_formatter_factory(options)
        self.formatter = formatter_factory(options.cwd, options.display_relative_path)

        # Without require_module, our _set_collections_basedir may fail
        self.runtime = Runtime(
            isolated=True,
            require_module=True,
            verbosity=options.verbosity,
        )
        self.reqs = Reqs("ansible-lint")
        package = "ansible-core"
        if not self.reqs.matches(
            package,
            str(self.runtime.version),
        ):  # pragma: no cover
            msg = f"ansible-lint requires {package}{','.join(str(x) for x in self.reqs[package])} and current version is {self.runtime.version}"
            logging.error(msg)
            sys.exit(RC.INVALID_CONFIG)

        # pylint: disable=import-outside-toplevel
        from ansiblelint.yaml_utils import load_yamllint_config  # noqa: 811, I001

        self.yamllint_config = load_yamllint_config()

    def render_matches(self, matches: list[MatchError]) -> None:
        """Display given matches (if they are not fixed)."""
        matches = [match for match in matches if not match.fixed]

        if isinstance(
            self.formatter,
            formatters.CodeclimateJSONFormatter | formatters.SarifFormatter,
        ):
            # If formatter CodeclimateJSONFormatter or SarifFormatter is chosen,
            # then print only the matches in JSON
            console.print(
                self.formatter.format_result(matches),
                markup=False,
                highlight=False,
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
                    console.print(self.formatter.apply(match), highlight=False)
        if fatal_matches:
            _logger.warning(
                "Listing %s violation(s) that are fatal",
                len(fatal_matches),
            )
            for match in fatal_matches:
                if not match.ignored:
                    console.print(self.formatter.apply(match), highlight=False)

        # If run under GitHub Actions we also want to emit output recognized by it.
        if os.getenv("GITHUB_ACTIONS") == "true" and os.getenv("GITHUB_WORKFLOW"):
            _logger.info(
                "GitHub Actions environment detected, adding annotations output...",
            )
            formatter = formatters.AnnotationsFormatter(self.options.cwd, True)
            for match in itertools.chain(fatal_matches, ignored_matches):
                console_stderr.print(
                    formatter.apply(match),
                    markup=False,
                    highlight=False,
                )

        # If sarif_file is set, we also dump the results to a sarif file.
        if self.options.sarif_file:
            sarif = formatters.SarifFormatter(self.options.cwd, True)
            json = sarif.format_result(matches)
            with Path.open(
                self.options.sarif_file,
                "w",
                encoding="utf-8",
            ) as sarif_file:
                sarif_file.write(json)

    def count_results(self, matches: list[MatchError]) -> SummarizedResults:
        """Count failures and warnings in matches."""
        result = SummarizedResults()

        for match in matches:
            # any ignores match counts as a warning
            if match.ignored:
                result.warnings += 1
                continue
            # tag can include a sub-rule id: `yaml[document-start]`
            # rule.id is the generic rule id: `yaml`
            # *rule.tags is the list of the rule's tags (categories): `style`
            if match.tag not in result.tag_stats:
                result.tag_stats[match.tag] = TagStats(
                    tag=match.tag,
                    count=1,
                    associated_tags=match.rule.tags,
                )
            else:
                result.tag_stats[match.tag].count += 1

            if {match.tag, match.rule.id, *match.rule.tags}.isdisjoint(
                self.options.warn_list,
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

    def report_outcome(
        self,
        result: LintResult,
        *,
        mark_as_success: bool = False,
    ) -> int:
        """Display information about how to skip found rules.

        Returns exit code, 2 if errors were found, 0 when only warnings were found.
        """
        msg = ""

        summary = self.count_results(result.matches)
        files_count, changed_files_count = self.count_lintables(result.files)

        matched_rules = self._get_matched_skippable_rules(result.matches)

        if matched_rules and self.options.generate_ignore:
            # ANSIBLE_LINT_IGNORE_FILE environment variable overrides default
            # dumping location in linter and is not documented or supported. We
            # use this only for testing purposes.
            ignore_file_path = Path(
                os.environ.get("ANSIBLE_LINT_IGNORE_FILE", IGNORE_FILE.default),
            )
            console_stderr.print(f"Writing ignore file to {ignore_file_path}")
            lines = set()
            for rule in result.matches:
                lines.add(f"{rule.filename} {rule.tag}\n")
            with ignore_file_path.open("w", encoding="utf-8") as ignore_file:
                ignore_file.write(
                    "# This file contains ignores rule violations for ansible-lint\n",
                )
                ignore_file.writelines(sorted(lines))
        elif matched_rules and not self.options.quiet:
            console_stderr.print(
                "Read [link=https://ansible.readthedocs.io/projects/lint/configuring/#ignoring-rules-for-entire-files]documentation[/link] for instructions on how to ignore specific rule violations.",
            )

        # Do not deprecate the old tags just yet. Why? Because it is not currently feasible
        # to migrate old tags to new tags. There are a lot of things out there that still
        # use ansible-lint 4 (for example, Ansible Galaxy and Automation Hub imports). If we
        # replace the old tags, those tools will report warnings. If we do not replace them,
        # ansible-lint 5 will report warnings.
        #
        # We can do the deprecation once the ecosystem caught up at least a bit.
        # for k, v in used_old_tags.items():
        #     _logger.warning(
        #         "error in the future.",
        #         k,
        #         v,

        if self.options.write_list and "yaml" in self.options.skip_list:
            _logger.warning(
                "You specified '--fix', but no files can be modified "
                "because 'yaml' is in 'skip_list'.",
            )

        if mark_as_success and summary.failures:
            mark_as_success = False

        if not self.options.quiet:
            console_stderr.print(render_yaml(msg))
            self.report_summary(
                summary,
                changed_files_count,
                files_count,
                is_success=mark_as_success,
            )
        if mark_as_success:
            if not files_count:
                # success without any file being analyzed is reported as failure
                # to match match, preventing accidents where linter was running
                # not doing anything due to misconfiguration.
                _logger.critical(
                    "Linter finished without analyzing any file, check configuration and arguments given.",
                )
                return RC.NO_FILES_MATCHED
            return RC.SUCCESS
        return RC.VIOLATIONS_FOUND

    def report_summary(  # pylint: disable=too-many-locals # noqa: C901
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
                rule_order[rule] = (idx, profile)
                idx += 1
        _logger.debug("Determined rule-profile order: %s", rule_order)
        failed_profiles = set()
        for tag, tag_stats in summary.tag_stats.items():
            if tag in rule_order:
                tag_stats.order, tag_stats.profile = rule_order.get(tag, (idx, ""))
            elif "[" in tag:
                tag_stats.order, tag_stats.profile = rule_order.get(
                    tag.split("[")[0],
                    (idx, ""),
                )
            if tag_stats.profile:
                failed_profiles.add(tag_stats.profile)
        summary.sort()

        if changed_files_count:
            console_stderr.print(f"Modified {changed_files_count} files.")

        # determine which profile passed
        summary.passed_profile = ""
        passed_profile_count = 0
        for profile in PROFILES:
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
                stars = f" Rating: {rating}/5 star"

            console_stderr.print(table)
            console_stderr.print()

        msg = "[green]Passed[/]" if is_success else "[red][bold]Failed[/][/]"

        msg += f": {summary.failures} failure(s), {summary.warnings} warning(s)"
        if summary.fixed:
            msg += f", and fixed {summary.fixed} issue(s)"
        msg += f" on {files_count} files."

        # Now we add some information about required and passed profile
        if self.options.profile:
            msg += f" Profile '{self.options.profile}' was required"
            if summary.passed_profile:
                if summary.passed_profile == self.options.profile:
                    msg += ", and it passed."
                else:
                    msg += f", but '{summary.passed_profile}' profile passed."
            else:
                msg += "."
        elif summary.passed_profile:
            msg += f" Last profile that met the validation criteria was '{summary.passed_profile}'."

        if stars:
            msg += stars

        # on offline mode and when run under pre-commit we do not want to
        # check for updates.
        if not self.options.offline and os.environ.get("PRE_COMMIT", "0") != "1":
            version_warning = get_version_warning()
            if version_warning:
                msg += f"\n{version_warning}"

        console_stderr.print(msg)


def choose_formatter_factory(
    options_list: Options,
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
def get_app(*, offline: bool | None = None, cached: bool = False) -> App:
    """Return the application instance, caching the return value."""
    # Avoids ever running the app initialization twice if cached argument
    # is mentioned.
    if cached:
        if offline is not None:
            msg = (
                "get_app should never be called with other arguments when cached=True."
            )
            raise RuntimeError(msg)
        if cached and _CACHED_APP is not None:
            return _CACHED_APP

    if offline is None:
        offline = default_options.offline

    if default_options.offline != offline:
        options = copy.deepcopy(default_options)
        options.offline = offline
    else:
        options = default_options

    app = App(options=options)
    # Make linter use the cache dir from compat
    options.cache_dir = app.runtime.cache_dir

    role_name_check = 0
    if "role-name" in app.options.warn_list:
        role_name_check = 1
    elif "role-name" in app.options.skip_list:
        role_name_check = 2

    # mocking must happen before prepare_environment or galaxy install might
    # fail.
    _perform_mockings(options=app.options)
    app.runtime.prepare_environment(
        install_local=(not offline),
        offline=offline,
        role_name_check=role_name_check,
    )

    return app
