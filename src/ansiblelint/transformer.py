"""Transformer implementation."""
import logging
import re
from typing import Dict, List, Set, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
# To make the type checkers happy, we import from ruamel.yaml.main instead.
from ruamel.yaml.main import YAML

from .errors import MatchError
from .file_utils import Lintable
from .runner import LintResult
from .skip_utils import load_data  # TODO: move load_data out of skip_utils

__all__ = ["Transformer"]

_logger = logging.getLogger(__name__)

_comment_line_re = re.compile(r"^ *#")


# Transformer is for transforms like runner is for rules
class Transformer:
    """Transformer class performs the fmt transformations."""

    def __init__(self, result: LintResult):
        """Initialize a Transformer instance."""
        # TODO: options for explict_start, indent_sequences
        self.explicit_start = True
        self.indent_sequences = True

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

        # NB: ruamel.yaml does not have typehints, so mypy complains about everything here.

        # configure yaml dump formatting
        yaml.explicit_start = True  # type: ignore[assignment]
        yaml.explicit_end = False  # type: ignore[assignment]

        # TODO: make the width configurable
        # yaml.width defaults to 80 which wraps longer lines in tests
        yaml.width = 120  # type: ignore[assignment]

        yaml.default_flow_style = False
        yaml.compact_seq_seq = (  # dash after dash
            True  # type: ignore[assignment]
        )
        yaml.compact_seq_map = (  # key after dash
            True  # type: ignore[assignment]
        )
        # yaml.indent() obscures the purpose of these vars:
        yaml.map_indent = 2  # type: ignore[assignment]
        yaml.sequence_indent = 4 if self.indent_sequences else 2  # type: ignore[assignment]
        yaml.sequence_dash_offset = yaml.sequence_indent - 2  # type: ignore[operator]

        # explicit_start=True + map_indent=2 + sequence_indent=2 + sequence_dash_offset=0
        # ---
        # - name: playbook
        #   loop:
        #   - item1
        #
        # explicit_start=True + map_indent=2 + sequence_indent=4 + sequence_dash_offset=2
        # ---
        #   - name: playbook
        #     loop:
        #       - item1

        for file, matches in self.matches_per_file.items():
            # str() convinces mypy that "text/yaml" is a valid Literal.
            # Otherwise, it thinks base_kind is one of playbook, meta, tasks, ...
            file_is_yaml = str(file.base_kind) == "text/yaml"

            if file_is_yaml:
                # load_data has an lru_cache, so using it should be cached vs using YAML().load() to reload
                data: Union[CommentedMap, CommentedSeq] = load_data(file.content)
                yaml.dump(data, file.path)
