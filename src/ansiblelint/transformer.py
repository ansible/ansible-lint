"""Transformer implementation."""
import logging
from typing import List, Optional, Set

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
# To make the type checkers happy, we import from ruamel.yaml.main instead.
from ruamel.yaml.main import YAML

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.runner import LintResult
from ansiblelint.yaml_utils import yaml_round_tripper

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
        self._yaml: Optional[YAML] = None

        self.matches: List[MatchError] = result.matches
        self.files: Set[Lintable] = result.files

    @property
    def yaml(self) -> YAML:
        if self._yaml is None:
            # TODO: Use options to configure yaml_round_tripper here.
            self._yaml = yaml_round_tripper()
        return self._yaml

    def run(self) -> None:
        """For each file, read it, execute transforms on it, then write it."""
