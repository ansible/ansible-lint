"""Runner implementation."""
import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, FrozenSet, Generator, List, Optional, Set, Union

import ansiblelint.file_utils
import ansiblelint.skip_utils
import ansiblelint.utils
from ansiblelint._internal.rules import LoadingFailureRule
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable

if TYPE_CHECKING:
    from ansiblelint.rules import RulesCollection


_logger = logging.getLogger(__name__)


@dataclass
class LintResult:
    """Class that tracks result of linting."""

    matches: List[MatchError]
    files: Set[str]


class Runner(object):
    """Runner class performs the linting process."""

    def __init__(
            self,
            rules: "RulesCollection",
            lintable: Union[Lintable, str],
            tags: FrozenSet[Any] = frozenset(),
            skip_list: Optional[FrozenSet[Any]] = frozenset(),
            exclude_paths: List[str] = [],
            verbosity: int = 0,
            checked_files: Optional[Set[str]] = None) -> None:
        """Initialize a Runner instance."""
        self.rules = rules
        self.playbooks: Set[Lintable] = set()

        # TODO(ssbarnea): Continue refactoring to make use of lintables
        playbook: str
        if isinstance(lintable, Lintable):
            playbook = str(lintable.path)
        else:
            playbook = lintable

        # assume role if directory
        if os.path.isdir(playbook):
            self.playbooks.add(Lintable(playbook, kind='role'))
            self.playbook_dir = playbook
        else:
            self.playbook_dir = os.path.dirname(playbook)
            if playbook.endswith("meta/main.yml"):
                file_type = "meta"
            else:
                file_type = "playbook"
            self.playbooks.add(Lintable(playbook, kind=file_type))  # type: ignore
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
        for playbook in self.playbooks:
            if self.is_excluded(str(playbook.path)) or playbook.kind == 'role':
                continue
            files.append(
                Lintable(
                    ansiblelint.file_utils.normpath(str(playbook.path)),
                    kind=playbook.kind))  # type: ignore
        matches = set(self._emit_matches(files))

        # remove duplicates from files list
        files = [value for n, value in enumerate(files) if value not in files[:n]]

        # remove files that have already been checked
        files = [x for x in files if x['path'] not in self.checked_files]
        for file in files:
            _logger.debug(
                "Examining %s of type %s",
                ansiblelint.file_utils.normpath(file.path),
                file.kind)
            matches = matches.union(
                self.rules.run(file, tags=set(self.tags),
                               skip_list=self.skip_list))
        # update list of checked files
        self.checked_files.update([str(x.path) for x in files])

        return sorted(matches)

    def _emit_matches(self, files: List[Lintable]) -> Generator[MatchError, None, None]:
        visited: Set = set()
        while visited != self.playbooks:
            for arg in self.playbooks - visited:
                try:
                    for child in ansiblelint.utils.find_children(arg, self.playbook_dir):
                        if self.is_excluded(str(child.path)):
                            continue
                        self.playbooks.add(child)
                        files.append(child)
                except MatchError as e:
                    e.rule = LoadingFailureRule()
                    yield e
                visited.add(arg)
