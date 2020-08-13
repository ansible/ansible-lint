"""Runner implementation."""
import logging
import os
from typing import TYPE_CHECKING, Any, FrozenSet, Generator, List, Set

import ansiblelint.file_utils
import ansiblelint.skip_utils
import ansiblelint.utils
from ansiblelint.errors import MatchError
from ansiblelint.rules.LoadingFailureRule import LoadingFailureRule

if TYPE_CHECKING:
    from ansiblelint.rules import RulesCollection


_logger = logging.getLogger(__name__)


class Runner(object):
    """Runner class performs the linting process."""

    def __init__(
            self,
            rules: "RulesCollection",
            playbook: str,
            tags: FrozenSet[Any],
            skip_list: FrozenSet[Any],
            exclude_paths: List[str],
            verbosity: int = 0,
            checked_files: Set[str] = None) -> None:
        """Initialize a Runner instance."""
        self.rules = rules
        self.playbooks = set()
        # assume role if directory
        if os.path.isdir(playbook):
            self.playbooks.add((os.path.join(playbook, ''), 'role'))
            self.playbook_dir = playbook
        else:
            self.playbooks.add((playbook, 'playbook'))
            self.playbook_dir = os.path.dirname(playbook)
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
            paths = ansiblelint.utils.expand_paths_vars(exclude_paths)
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
        files = list()
        for playbook in self.playbooks:
            if self.is_excluded(playbook[0]) or playbook[1] == 'role':
                continue
            files.append({'path': ansiblelint.file_utils.normpath(playbook[0]),
                          'type': playbook[1],
                          # add an absolute path here, so rules are able to validate if
                          # referenced files exist
                          'absolute_directory': os.path.dirname(playbook[0])})
        matches = set(self._emit_matches(files))

        # remove duplicates from files list
        files = [value for n, value in enumerate(files) if value not in files[:n]]

        # remove files that have already been checked
        files = [x for x in files if x['path'] not in self.checked_files]
        for file in files:
            _logger.debug(
                "Examining %s of type %s",
                ansiblelint.file_utils.normpath(file['path']),
                file['type'])
            matches = matches.union(
                self.rules.run(file, tags=set(self.tags),
                               skip_list=self.skip_list))
        # update list of checked files
        self.checked_files.update([x['path'] for x in files])

        return sorted(matches)

    def _emit_matches(self, files: List) -> Generator[MatchError, None, None]:
        visited: Set = set()
        while visited != self.playbooks:
            for arg in self.playbooks - visited:
                try:
                    for child in ansiblelint.utils.find_children(arg, self.playbook_dir):
                        if self.is_excluded(child['path']):
                            continue
                        self.playbooks.add((child['path'], child['type']))
                        files.append(child)
                except MatchError as e:
                    e.rule = LoadingFailureRule
                    yield e
                visited.add(arg)
