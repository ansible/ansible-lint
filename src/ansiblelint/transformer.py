"""Transformer implementation."""
import logging
import re
from typing import Dict, List, Optional, Set, Union, cast

from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.emitter import Emitter

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
# To make the type checkers happy, we import from ruamel.yaml.main instead.
from ruamel.yaml.main import YAML

from .errors import MatchError
from .file_utils import Lintable
from .runner import LintResult
from .skip_utils import load_data  # TODO: move load_data out of skip_utils

__all__ = ["Transformer"]

_logger = logging.getLogger(__name__)

# ruamel.yaml only preserves empty (no whitespace) blank lines
# (ie "/n/n" becomes "/n/n" but "/n  /n" becomes "/n").
# So, we need to identify whitespace-only lines to drop spaces before reading.
_whitespace_only_lines_re = re.compile(r"^ +$", re.MULTILINE)


class FormattedEmitter(Emitter):
    """Emitter that applies custom formatting rules when dumping YAML.

    Root-level sequences are never indented.
    All subsequent levels are indented as configured (normal ruamel.yaml behavior).

    Earlier implementations used dedent on ruamel.yaml's dumped output,
    but string magic like that had a ton of problematic edge cases.
    """

    _sequence_indent = 2
    _sequence_dash_offset = 0  # Should be _sequence_indent - 2

    @property
    def _is_root_level(self) -> bool:
        """Return True if this is the root level of the yaml document.

        Here, root level means the outermost sequence or map of the document.
        """
        return self.column < 2

    # NB: mypy does not support overriding attributes with properties yet:
    #     https://github.com/python/mypy/issues/4125
    #     To silence we have to ignore[override] both the @property and the method.

    @property  # type: ignore[override]
    def best_sequence_indent(self) -> int:  # type: ignore[override]
        """Return the configured sequence_indent or 2 for root level."""
        return 2 if self._is_root_level else self._sequence_indent

    @best_sequence_indent.setter
    def best_sequence_indent(self, value: int) -> None:
        """Configure how many columns to indent each sequence item (including the '-')."""
        self._sequence_indent = value

    @property  # type: ignore[override]
    def sequence_dash_offset(self) -> int:  # type: ignore[override]
        """Return the configured sequence_dash_offset or 2 for root level."""
        return 0 if self._is_root_level else self._sequence_dash_offset

    @sequence_dash_offset.setter
    def sequence_dash_offset(self, value: int) -> None:
        """Configure how many spaces to put before each sequence item's '-'."""
        self._sequence_dash_offset = value


# Transformer is for transforms like runner is for rules
class Transformer:
    """Transformer class performs the fmt transformations.

    The Transformer is similar to the ``ansiblelint.runner.Runner`` which manages
    running each of the rules. We only expect there to be one ``Transformer`` instance
    which should be instantiated from the main entrypoint function.

    In the future, the transformer will be responsible for running transforms for each
    of the rule matches. For now, it just reads/writes YAML files which is a
    pre-requisite for the planned rule-specific transforms.
    """

    def __init__(self, result: LintResult):
        """Initialize a Transformer instance."""
        # TODO: Make config options for: explict_start, indent_sequences, yaml_width, etc
        self.yaml_explicit_start = True
        self.yaml_explicit_end = False
        self.yaml_indent_sequences = True
        # yaml.width defaults to 80 which wraps longer lines in tests
        self.yaml_width = 120

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

        self._yaml: Optional[YAML] = None

    @property
    def yaml(self) -> YAML:
        """Return a configured ``ruamel.yaml.YAML`` instance.

        ``ruamel.yaml.YAML`` uses attributes to configure how it dumps yaml files.
        Some of these settings can be confusing, so here are examples of how different
        settings will affect the dumped yaml.

        This example does not indent any sequences:

        .. code:: python

            yaml.explicit_start=True
            yaml.map_indent=2
            yaml.sequence_indent=2
            yaml.sequence_dash_offset=0

        .. code:: yaml

            ---
            - name: playbook
              loop:
              - item1

        This example indents all sequences including the root-level:

        .. code:: python

            yaml.explicit_start=True
            yaml.map_indent=2
            yaml.sequence_indent=4
            yaml.sequence_dash_offset=2
            # yaml.Emitter defaults to ruamel.yaml.emitter.Emitter

        .. code:: yaml

            ---
              - name: playbook
                loop:
                  - item1

        This example indents all sequences except at the root-level:

        .. code:: python

            yaml.explicit_start=True
            yaml.map_indent=2
            yaml.sequence_indent=4
            yaml.sequence_dash_offset=2
            yaml.Emitter = FormattedEmitter  # custom Emitter prevents root-level indents

        .. code:: yaml

            ---
            - name: playbook
              loop:
                - item1
        """
        if self._yaml is not None:
            return self._yaml

        # ruamel.yaml rt=round trip (preserves comments while allowing for modification)
        yaml = YAML(typ="rt")

        # NB: ruamel.yaml does not have typehints, so mypy complains about everything here.

        # configure yaml dump formatting
        yaml.explicit_start = self.yaml_explicit_start  # type: ignore[assignment]
        yaml.explicit_end = self.yaml_explicit_end  # type: ignore[assignment]
        yaml.width = self.yaml_width  # type: ignore[assignment]

        yaml.default_flow_style = False
        yaml.compact_seq_seq = (  # dash after dash
            True  # type: ignore[assignment]
        )
        yaml.compact_seq_map = (  # key after dash
            True  # type: ignore[assignment]
        )
        # Do not use yaml.indent() as it obscures the purpose of these vars:
        yaml.map_indent = 2  # type: ignore[assignment]
        yaml.sequence_indent = 4 if self.yaml_indent_sequences else 2  # type: ignore[assignment]
        yaml.sequence_dash_offset = yaml.sequence_indent - 2  # type: ignore[operator]

        if self.yaml_indent_sequences:  # in the future: or other formatting options
            # For root-level sequences, FormattedEmitter overrides sequence_indent
            # and sequence_dash_offset to prevent root-level indents.
            yaml.Emitter = FormattedEmitter

        self._yaml = yaml
        return yaml

    def run(self) -> None:
        """For each file, read it, execute fmt transforms on it, then write it."""
        for file, matches in self.matches_per_file.items():
            # str() convinces mypy that "text/yaml" is a valid Literal.
            # Otherwise, it thinks base_kind is one of playbook, meta, tasks, ...
            file_is_yaml = str(file.base_kind) == "text/yaml"

            try:
                data: Union[CommentedMap, CommentedSeq, str] = file.content
            except (UnicodeDecodeError, IsADirectoryError):
                # we hit a binary file (eg a jar or tar.gz) or a directory
                data = ""
                file_is_yaml = False

            if file_is_yaml:
                # ruamel.yaml only preserves empty (no whitespace) blank lines.
                # So, drop spaces in whitespace-only lines. ("\n  \n" -> "\n\n")
                data = _whitespace_only_lines_re.sub("", cast(str, data))
                # load_data has an lru_cache, so using it should be cached vs using YAML().load() to reload
                data = load_data(data)
                self.yaml.dump(data, file.path)
