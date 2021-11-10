"""Transformer implementation."""
from typing import Dict, List, Set, Union

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
from ruamel.yaml import YAML  # type: ignore
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from .errors import MatchError
from .file_utils import Lintable
from .runner import LintResult
from .skip_utils import load_data  # TODO: move load_data out of skip_utils


# Transformer is for transforms like runner is for rules
class Transformer:
    """Transformer class performs the fmt transformations."""

    def __init__(
        self,
        result: LintResult,
    ):
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
        """Execute the fmt transforms."""
        # ruamel.yaml rt=round trip (preserves comments while allowing for modification)
        yaml = YAML(typ="rt")

        # configure yaml dump formatting
        yaml.explicit_start = True
        yaml.explicit_end = False
        mapping_indent = sequence_indent = 2
        offset_indent = sequence_indent - 2
        yaml.indent(mapping=mapping_indent, sequence=sequence_indent, offset=offset_indent)

        # explicit_start=True + indent(mapping=2, sequence=2, offset=0):
        # ---
        # - name: playbook
        #   loop:
        #   - item1
        #
        # explicit_start=True + indent(mapping=2, sequence=4, offset=2):
        # ---
        #   - name: playbook
        #     loop:
        #       - item1

        for file, matches in self.matches_per_file.items():
            # load_data has an lru_cache, so using it should be cached vs using YAML().load() to reload
            ruamel_data: Union[CommentedMap, CommentedSeq] = load_data(file.content)
            yaml.dump(ruamel_data, file.path)
