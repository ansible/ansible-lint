"""Runner implementation."""
import logging
import multiprocessing
import multiprocessing.pool
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, FrozenSet, Generator, List, Optional, Set, Union

import ansiblelint.skip_utils
import ansiblelint.utils
from ansiblelint._internal.rules import LoadingFailureRule
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.AnsibleSyntaxCheckRule import AnsibleSyntaxCheckRule

if TYPE_CHECKING:
    from argparse import Namespace

    from ansiblelint.rules import RulesCollection

_logger = logging.getLogger(__name__)


@dataclass
class LintResult:
    """Class that tracks result of linting."""

    matches: List[MatchError]
    files: Set[str]


class Runner:
    """Runner class performs the linting process."""

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            *lintables: Union[Lintable, str],
            rules: "RulesCollection",
            tags: FrozenSet[Any] = frozenset(),
            skip_list: List[str] = [],
            exclude_paths: List[str] = [],
            verbosity: int = 0,
            checked_files: Optional[Set[str]] = None) -> None:
        """Initialize a Runner instance."""
        self.rules = rules
        self.lintables: Set[Lintable] = set()

        # Assure consistent type
        for item in lintables:
            if not isinstance(item, Lintable):
                item = Lintable(item)
            self.lintables.add(item)

        self.tags = tags
        self.skip_list = skip_list
        self._update_exclude_paths(exclude_paths)
        self.verbosity = verbosity
        if checked_files is None:
            checked_files = set()
        self.checked_files = checked_files

    def _update_exclude_paths(self, exclude_paths: List[str]) -> None:
        if exclude_paths:
            # These will be (potentially) relative paths
            paths = ansiblelint.file_utils.expand_paths_vars(exclude_paths)
            # Since ansiblelint.utils.find_children returns absolute paths,
            # and the list of files we create in `Runner.run` can contain both
            # relative and absolute paths, we need to cover both bases.
            self.exclude_paths = paths + [os.path.abspath(p) for p in paths]
        else:
            self.exclude_paths = []

    def is_excluded(self, file_path: str) -> bool:
        """Verify if a file path should be excluded."""
        # Any will short-circuit as soon as something returns True, but will
        # be poor performance for the case where the path under question is
        # not excluded.
        return any(file_path.startswith(path) for path in self.exclude_paths)

    def run(self) -> List[MatchError]:
        """Execute the linting process."""
        files: List[Lintable] = list()
        matches: List[MatchError] = list()

        # -- phase 1 : syntax check in parallel --
        def worker(lintable: Lintable) -> List[MatchError]:
            return AnsibleSyntaxCheckRule._get_ansible_syntax_check_matches(lintable)

        # playbooks: List[Lintable] = []
        for lintable in self.lintables:
            if self.is_excluded(str(lintable.path.resolve())) or lintable.kind != 'playbook':
                continue
            files.append(lintable)

        pool = multiprocessing.pool.ThreadPool(processes=multiprocessing.cpu_count())
        return_list = pool.map(worker, files, chunksize=1)
        pool.close()
        pool.join()
        for data in return_list:
            matches.extend(data)

        matches.extend(self._emit_matches(files))
        # -- phase 2 ---
        if not matches:  # do our processing only when ansible syntax check passed

            matches.extend(self._emit_matches(files))

            # remove duplicates from files list
            files = [value for n, value in enumerate(files) if value not in files[:n]]

            for file in files:
                if str(file.path) in self.checked_files:
                    continue
                _logger.debug(
                    "Examining %s of type %s",
                    ansiblelint.file_utils.normpath(file.path),
                    file.kind)

                matches.extend(
                    self.rules.run(file, tags=set(self.tags),
                                   skip_list=self.skip_list))

        # update list of checked files
        self.checked_files.update([str(x.path) for x in files])

        return sorted(set(matches))

    def _emit_matches(self, files: List[Lintable]) -> Generator[MatchError, None, None]:
        visited: Set[Lintable] = set()
        while visited != self.lintables:
            for lintable in self.lintables - visited:
                try:
                    for child in ansiblelint.utils.find_children(lintable):
                        if self.is_excluded(str(child.path)):
                            continue
                        self.lintables.add(child)
                        files.append(child)
                except MatchError as e:
                    e.rule = LoadingFailureRule()
                    yield e
                except AttributeError:
                    yield MatchError(
                        filename=str(lintable.path),
                        rule=LoadingFailureRule()
                    )
                visited.add(lintable)


def _get_matches(rules: "RulesCollection", options: "Namespace") -> LintResult:

    lintables = ansiblelint.utils.get_lintables(options=options, args=options.lintables)

    matches = list()
    checked_files: Set[str] = set()
    runner = Runner(
        *lintables,
        rules=rules,
        tags=options.tags,
        skip_list=options.skip_list,
        exclude_paths=options.exclude_paths,
        verbosity=options.verbosity,
        checked_files=checked_files)
    matches.extend(runner.run())

    # Assure we do not print duplicates and the order is consistent
    matches = sorted(set(matches))

    return LintResult(matches=matches, files=checked_files)
