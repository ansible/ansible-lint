"""Transformer implementation."""
import logging
from typing import List, Set

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.runner import LintResult

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

    def run(self) -> None:
        """For each file, read it, execute transforms on it, then write it."""
