"""Runner implementation."""
from __future__ import annotations

import logging
import multiprocessing
import multiprocessing.pool
import os
import warnings
from dataclasses import dataclass
from fnmatch import fnmatch
from typing import TYPE_CHECKING, Any

from ansible_compat.runtime import AnsibleWarning

import ansiblelint.skip_utils
import ansiblelint.utils
from ansiblelint._internal.rules import LoadingFailureRule, WarningRule
from ansiblelint.constants import States
from ansiblelint.errors import LintWarning, MatchError, WarnSource
from ansiblelint.file_utils import Lintable, expand_dirs_in_lintables
from ansiblelint.rules.syntax_check import AnsibleSyntaxCheckRule

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from ansiblelint.config import Options
    from ansiblelint.rules import RulesCollection

_logger = logging.getLogger(__name__)


@dataclass
class LintResult:
    """Class that tracks result of linting."""

    matches: list[MatchError]
    files: set[Lintable]


class Runner:
    """Runner class performs the linting process."""

    # pylint: disable=too-many-arguments,too-many-instance-attributes
    def __init__(
        self,
        *lintables: Lintable | str | Path,
        rules: RulesCollection,
        tags: frozenset[Any] = frozenset(),
        skip_list: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        verbosity: int = 0,
        checked_files: set[Lintable] | None = None,
        project_dir: str | None = None,
    ) -> None:
        """Initialize a Runner instance."""
        self.rules = rules
        self.lintables: set[Lintable] = set()
        self.project_dir = os.path.abspath(project_dir) if project_dir else None

        if skip_list is None:
            skip_list = []
        if exclude_paths is None:
            exclude_paths = []

        # Assure consistent type and configure given lintables as explicit (so
        # excludes paths would not apply on them).
        for item in lintables:
            if not isinstance(item, Lintable):
                item = Lintable(item)
            item.explicit = True
            self.lintables.add(item)

        # Expand folders (roles) to their components
        expand_dirs_in_lintables(self.lintables)

        self.tags = tags
        self.skip_list = skip_list
        self._update_exclude_paths(exclude_paths)
        self.verbosity = verbosity
        if checked_files is None:
            checked_files = set()
        self.checked_files = checked_files

    def _update_exclude_paths(self, exclude_paths: list[str]) -> None:
        if exclude_paths:
            # These will be (potentially) relative paths
            paths = ansiblelint.file_utils.expand_paths_vars(exclude_paths)
            # Since ansiblelint.utils.find_children returns absolute paths,
            # and the list of files we create in `Runner.run` can contain both
            # relative and absolute paths, we need to cover both bases.
            self.exclude_paths = paths + [os.path.abspath(p) for p in paths]
        else:
            self.exclude_paths = []

    def is_excluded(self, lintable: Lintable) -> bool:
        """Verify if a file path should be excluded."""
        # Any will short-circuit as soon as something returns True, but will
        # be poor performance for the case where the path under question is
        # not excluded.

        # Exclusions should be evaluated only using absolute paths in order
        # to work correctly.

        # Explicit lintables are never excluded
        if lintable.explicit:
            return False

        abs_path = str(lintable.abspath)
        if self.project_dir and not abs_path.startswith(self.project_dir):
            _logger.debug(
                "Skipping %s as it is outside of the project directory.",
                abs_path,
            )
            return True

        return any(
            abs_path.startswith(path)
            or lintable.path.match(path)
            or fnmatch(str(abs_path), path)
            or fnmatch(str(lintable), path)
            for path in self.exclude_paths
        )

    def run(self) -> list[MatchError]:
        """Execute the linting process."""
        matches: list[MatchError] = []
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            matches = self._run()
            for warn in captured_warnings:
                # Silence Ansible runtime warnings that are unactionable
                # https://github.com/ansible/ansible-lint/issues/3216
                if warn.category is AnsibleWarning and isinstance(warn.source, dict):
                    msg = warn.source["msg"]
                    if msg.startswith(
                        "Falling back to Ansible unique filter as Jinja2 one failed",
                    ):
                        continue
                # For the moment we are ignoring deprecation warnings as Ansible
                # modules outside current content can generate them and user
                # might not be able to do anything about them.
                if warn.category is DeprecationWarning:
                    continue
                if warn.category is LintWarning:
                    filename: None | Lintable = None
                    if isinstance(warn.source, WarnSource):
                        match = MatchError(
                            message=warn.source.message or warn.category.__name__,
                            rule=WarningRule(),
                            filename=warn.source.filename.filename,
                            tag=warn.source.tag,
                            lineno=warn.source.lineno,
                        )
                    else:
                        filename = warn.source
                        match = MatchError(
                            message=warn.message
                            if isinstance(warn.message, str)
                            else "?",
                            rule=WarningRule(),
                            filename=str(filename),
                        )
                    matches.append(match)
                    continue
                _logger.warning(
                    "%s:%s %s %s",
                    warn.filename,
                    warn.lineno or 1,
                    warn.category.__name__,
                    warn.message,
                )
        return matches

    def _run(self) -> list[MatchError]:
        """Run the linting (inner loop)."""
        files: list[Lintable] = []
        matches: list[MatchError] = []

        # remove exclusions
        for lintable in self.lintables.copy():
            if self.is_excluded(lintable):
                _logger.debug("Excluded %s", lintable)
                self.lintables.remove(lintable)
                continue
            if isinstance(lintable.data, States) and lintable.exc:
                lintable.exc.__class__.__name__.lower()
                matches.append(
                    MatchError(
                        lintable=lintable,
                        message=str(lintable.exc),
                        details=str(lintable.exc.__cause__),
                        rule=LoadingFailureRule(),
                        tag=f"load-failure[{lintable.exc.__class__.__name__.lower()}]",
                    ),
                )
                lintable.stop_processing = True
            # identify missing files/folders
            if not lintable.path.exists():
                matches.append(
                    MatchError(
                        lintable=lintable,
                        message="File or directory not found.",
                        rule=LoadingFailureRule(),
                        tag="load-failure[not-found]",
                    ),
                )

        # -- phase 1 : syntax check in parallel --
        def worker(lintable: Lintable) -> list[MatchError]:
            # pylint: disable=protected-access
            return AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(  # noqa: SLF001
                lintable,
            )

        for lintable in self.lintables:
            if lintable.kind not in ("playbook", "role") or lintable.stop_processing:
                continue
            files.append(lintable)

        # avoid resource leak warning, https://github.com/python/cpython/issues/90549
        # pylint: disable=unused-variable
        global_resource = multiprocessing.Semaphore()  # noqa: F841

        pool = multiprocessing.pool.ThreadPool(processes=multiprocessing.cpu_count())
        return_list = pool.map(worker, files, chunksize=1)
        pool.close()
        pool.join()
        for data in return_list:
            matches.extend(data)

        # -- phase 2 ---
        if not matches:
            # do our processing only when ansible syntax check passed in order
            # to avoid causing runtime exceptions. Our processing is not as
            # resilient to be able process garbage.
            matches.extend(self._emit_matches(files))

            # remove duplicates from files list
            files = [value for n, value in enumerate(files) if value not in files[:n]]

            for file in self.lintables:
                if file in self.checked_files or not file.kind:
                    continue
                _logger.debug(
                    "Examining %s of type %s",
                    ansiblelint.file_utils.normpath(file.path),
                    file.kind,
                )

                matches.extend(
                    self.rules.run(file, tags=set(self.tags), skip_list=self.skip_list),
                )

        # update list of checked files
        self.checked_files.update(self.lintables)

        # remove any matches made inside excluded files
        matches = list(
            filter(
                lambda match: not self.is_excluded(match.lintable)
                and hasattr(match, "lintable")
                and match.tag not in match.lintable.line_skips[match.lineno],
                matches,
            ),
        )

        return sorted(set(matches))

    def _emit_matches(self, files: list[Lintable]) -> Generator[MatchError, None, None]:
        visited: set[Lintable] = set()
        while visited != self.lintables:
            for lintable in self.lintables - visited:
                try:
                    children = ansiblelint.utils.find_children(lintable)
                    for child in children:
                        if self.is_excluded(child):
                            continue
                        self.lintables.add(child)
                        files.append(child)
                except MatchError as exc:
                    if not exc.filename:  # pragma: no branch
                        exc.filename = str(lintable.path)
                    exc.rule = LoadingFailureRule()
                    yield exc
                except AttributeError:
                    yield MatchError(lintable=lintable, rule=LoadingFailureRule())
                visited.add(lintable)


def _get_matches(rules: RulesCollection, options: Options) -> LintResult:
    lintables = ansiblelint.utils.get_lintables(opts=options, args=options.lintables)

    for rule in rules:
        if "unskippable" in rule.tags:
            for entry in (*options.skip_list, *options.warn_list):
                if rule.id == entry or entry.startswith(f"{rule.id}["):
                    msg = f"Rule '{rule.id}' is unskippable, you cannot use it in 'skip_list' or 'warn_list'. Still, you could exclude the file."
                    raise RuntimeError(msg)
    matches = []
    checked_files: set[Lintable] = set()
    runner = Runner(
        *lintables,
        rules=rules,
        tags=frozenset(options.tags),
        skip_list=options.skip_list,
        exclude_paths=options.exclude_paths,
        verbosity=options.verbosity,
        checked_files=checked_files,
        project_dir=options.project_dir,
    )
    matches.extend(runner.run())

    # Assure we do not print duplicates and the order is consistent
    matches = sorted(set(matches))

    # Convert reported filenames into human readable ones, so we hide the
    # fact we used temporary files when processing input from stdin.
    for match in matches:
        for lintable in lintables:
            if match.filename == lintable.filename:
                match.filename = lintable.name
                break

    return LintResult(matches=matches, files=checked_files)
