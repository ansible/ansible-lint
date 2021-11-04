from typing import Dict, List, Optional, Set, Union

import ruamel.yaml
from ruamel.yaml.comments import CommentedSeq, CommentedMap

from .errors import MatchError
from .file_utils import Lintable
from .runner import LintResult
# TODO: move load_data out of skip_utils
from .skip_utils import load_data


# Transformer is for transforms like runner is for rules
class Transformer:
    def __init__(
        self,
        result: LintResult,
    ):
        self.matches: List[MatchError] = result.matches
        self.files: Set[Lintable] = result.files

        file: Lintable
        lintables: Dict[str, Lintable] = {file.filename: file for file in result.files}
        self.matches_per_file: Dict[Lintable, List[MatchError]] = {file: [] for file in result.files}

        for match in self.matches:
            try:
                lintable = lintables[match.filename]
            except KeyError:
                # we shouldn't get here, but this is easy to recover from so do that.
                lintable = Lintable(match.filename)
                self.matches_per_file[lintable] = []
            self.matches_per_file[lintable].append(match)

    def run(self):
        # ruamel.yaml rt=round trip (preserves comments while allowing for modification)
        yaml = ruamel.yaml.YAML(typ="rt")

        for file, matches in self.matches_per_file.items():
            ruamel_data: Union[CommentedMap, CommentedSeq] = load_data(file.content)
            yaml.dump(ruamel_data, file.path)
