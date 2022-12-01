"""Runner implementation."""
from __future__ import annotations

import logging
import multiprocessing
import multiprocessing.pool
import os
from dataclasses import dataclass
from fnmatch import fnmatch
from typing import TYPE_CHECKING, Any, Generator

import ansiblelint.skip_utils
import ansiblelint.utils
from ansiblelint._internal.rules import LoadingFailureRule
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable, expand_dirs_in_lintables
from ansiblelint.rules.syntax_check import AnsibleSyntaxCheckRule

if TYPE_CHECKING:
    from argparse import Namespace

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
        *lintables: Lintable | str,
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

        # Assure consistent type
        for item in lintables:
            if not isinstance(item, Lintable):
                item = Lintable(item)
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
        if not lintable:
            return False

        abs_path = str(lintable.abspath)
        if self.project_dir and not abs_path.startswith(self.project_dir):
            _logger.debug(
                "Skipping %s as it is outside of the project directory.", abs_path
            )
            return True

        return any(
            abs_path.startswith(path)
            or lintable.path.match(path)
            or fnmatch(str(abs_path), path)
            or fnmatch(str(lintable), path)
            for path in self.exclude_paths
        )

    def run(self) -> list[MatchError]:  # noqa: C901
        """Execute the linting process."""
        files: list[Lintable] = []
        matches: list[MatchError] = []

        # remove exclusions
        for lintable in self.lintables.copy():
            if self.is_excluded(lintable):
                _logger.debug("Excluded %s", lintable)
                self.lintables.remove(lintable)
                continue
            try:
                lintable.data
            except (RuntimeError, FileNotFoundError) as exc:
                matches.append(
                    MatchError(
                        filename=lintable,
                        message=str(exc),
                        details=str(exc.__cause__),
                        rule=LoadingFailureRule(),
                    )
                )
                lintable.stop_processing = True

        # -- phase 1 : syntax check in parallel --
        def worker(lintable: Lintable) -> list[MatchError]:
            # pylint: disable=protected-access
            return AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(lintable)

        # playbooks: List[Lintable] = []
        for lintable in self.lintables:
            if lintable.kind != "playbook" or lintable.stop_processing:
                continue
            files.append(lintable)

        # avoid resource leak warning, https://github.com/python/cpython/issues/90549
        # pylint: disable=unused-variable
        global_resource = multiprocessing.Semaphore()

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
                    self.rules.run(file, tags=set(self.tags), skip_list=self.skip_list)
                )

        # update list of checked files
        self.checked_files.update(self.lintables)

        # remove any matches made inside excluded files
        matches = list(
            filter(
                lambda match: not self.is_excluded(Lintable(match.filename))
                and hasattr(match, "lintable")
                and match.tag not in match.lintable.line_skips[match.linenumber],
                matches,
            )
        )

        return sorted(set(matches))

    def _emit_matches(self, files: list[Lintable]) -> Generator[MatchError, None, None]:
        visited: set[Lintable] = set()
        while visited != self.lintables:
            for lintable in self.lintables - visited:
                try:
                    for child in ansiblelint.utils.find_children(lintable):
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
                    yield MatchError(filename=lintable, rule=LoadingFailureRule())
                visited.add(lintable)


def _get_matches(rules: RulesCollection, options: Namespace) -> LintResult:

    lintables = ansiblelint.utils.get_lintables(opts=options, args=options.lintables)

    matches = []
    checked_files: set[Lintable] = set()
    runner = Runner(
        *lintables,
        rules=rules,
        tags=options.tags,
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
