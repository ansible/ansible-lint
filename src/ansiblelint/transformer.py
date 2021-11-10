"""Transformer implementation."""
import logging
import re
from textwrap import dedent
from typing import Dict, List, Set, Union

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
from ruamel.yaml import YAML  # type: ignore
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from .errors import MatchError
from .file_utils import Lintable
from .runner import LintResult
from .skip_utils import load_data  # TODO: move load_data out of skip_utils
from .transforms import Transform, TransformsCollection

_logger = logging.getLogger(__name__)

_comment_line_re = re.compile(r"^ *#")


# Transformer is for transforms like runner is for rules
class Transformer:
    """Transformer class performs the fmt transformations."""

    def __init__(
        self,
        result: LintResult,
        transforms: TransformsCollection,
    ):
        """Initialize a Transformer instance."""
        # TODO: options for explict_start, indent_sequences
        self.explicit_start = True
        self.indent_sequences = True

        self.matches: List[MatchError] = result.matches
        self.files: Set[Lintable] = result.files
        self.transforms = transforms

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

    def run(self, fmt_all_files=True) -> None:
        """Execute the fmt transforms."""
        # ruamel.yaml rt=round trip (preserves comments while allowing for modification)
        yaml = YAML(typ="rt")

        # configure yaml dump formatting
        yaml.explicit_start = (
            False  # explicit_start is handled in self._final_yaml_transform()
        )
        yaml.explicit_end = False
        yaml.default_flow_style = False
        yaml.compact_seq_seq = True  # dash after dash
        yaml.compact_seq_map = True  # key after dash
        # yaml.indent() obscures the purpose of these vars:
        yaml.map_indent = 2
        yaml.sequence_indent = 4 if self.indent_sequences else 2
        yaml.sequence_dash_offset = yaml.sequence_indent - 2

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
            # matches can be empty if no LintErrors were found.
            # However, we can still fmt the yaml file
            if not fmt_all_files and not matches:
                continue
            # load_data has an lru_cache, so using it should be cached vs using YAML().load() to reload
            ruamel_data: Union[CommentedMap, CommentedSeq] = load_data(file.content)
            for match in sorted(matches):
                transforms: List[Transform] = self.transforms.get_transforms_for(match)
                if not transforms:
                    continue
                for transform in transforms:
                    transform(match, ruamel_data)
            yaml.dump(ruamel_data, file.path, transform=self._final_yaml_transform)

    def _final_yaml_transform(self, text: str) -> str:
        """
        This ensures that top-level sequences are not over-indented.

        In order to make that work, we cannot delegate adding the yaml explict_start
        to ruamel.yaml or dedent() won't have anything to work with.
        Instead, we add the explicit_start here.
        """
        text_lines = text.splitlines(keepends=True)
        dedented_lines = dedent(text).splitlines(keepends=True)

        # preserve the indents for comment lines (do not dedent them)
        for i, line in enumerate(text_lines):
            if _comment_line_re.match(line):
                dedented_lines[i] = line

        text = "".join(dedented_lines)
        if self.explicit_start:
            text = "---\n" + text
        return text
