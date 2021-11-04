"""Transformer implementation."""
import logging
from typing import Dict, List, Set, Union

from ruamel.yaml.comments import CommentedSeq, CommentedMap

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.runner import LintResult
from ansiblelint.yaml_utils import FormattedYAML

__all__ = ["Transformer"]

_logger = logging.getLogger(__name__)


class Transformer:
    """Transformer class marshals transformations.

    The Transformer is similar to the ``ansiblelint.runner.Runner`` which manages
    running each of the rules. We only expect there to be one ``Transformer`` instance
    which should be instantiated from the main entrypoint function.
    """

    def __init__(self, result: LintResult):
        """Initialize a Transformer instance."""
        self.matches: List[MatchError] = result.matches
        self.files: Set[Lintable] = result.files

        file: Lintable
        lintables: Dict[str, Lintable] = {file.filename: file for file in result.files}
        self.matches_per_file: Dict[Lintable, List[MatchError]] = {
            file: [] for file in result.files
        }

        for match in self.matches:
            try:
                lintable = lintables[match.filename]
            except KeyError:
                # we shouldn't get here, but this is easy to recover from so do that.
                lintable = Lintable(match.filename)
                self.matches_per_file[lintable] = []
            self.matches_per_file[lintable].append(match)

    def run(self) -> None:
        """For each file, read it, execute transforms on it, then write it."""
        yaml = FormattedYAML()
        for file, matches in self.matches_per_file.items():
            if file.base_kind == "text/yaml":
                ruamel_data: Union[CommentedMap, CommentedSeq] = yaml.loads(file.content)
                file.content = yaml.dumps(ruamel_data)
                file.write()
