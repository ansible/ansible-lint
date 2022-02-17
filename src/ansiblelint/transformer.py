"""Transformer implementation."""
import logging
from typing import Any, List, Optional, Set

from ruamel.yaml.emitter import Emitter

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
# To make the type checkers happy, we import from ruamel.yaml.main instead.
from ruamel.yaml.main import YAML

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.runner import LintResult

__all__ = ["Transformer"]

_logger = logging.getLogger(__name__)


def _final_yaml_transform(text: str) -> str:
    """Transform YAML string before writing to file.

    Ansible uses PyYAML which only supports YAML 1.1, so we dump YAML 1.1.
    But we don't want "%YAML 1.1" at the start, so drop that.
    """
    prefix = "%YAML 1.1\n"
    prefix_len = len(prefix)
    if text.startswith(prefix):
        return text[prefix_len:]
    return text


class FormattedEmitter(Emitter):
    """Emitter that applies custom formatting rules when dumping YAML.

    Differences from ruamel.yaml defaults:

      - indentation of root-level sequences
      - prefer double-quoted scalars over single-quoted scalars

    This ensures that root-level sequences are never indented.
    All subsequent levels are indented as configured (normal ruamel.yaml behavior).

    Earlier implementations used dedent on ruamel.yaml's dumped output,
    but string magic like that had a ton of problematic edge cases.
    """

    preferred_quote = '"'  # either " or '

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

    def choose_scalar_style(self) -> Any:
        """Select how to quote scalars if needed."""
        style = super().choose_scalar_style()
        if style != "'":
            # block scalar, double quoted, etc.
            return style
        if '"' in self.event.value:
            return "'"
        return self.preferred_quote


class Transformer:
    """Transformer class marshals transformations.

    The Transformer is similar to the ``ansiblelint.runner.Runner`` which manages
    running each of the rules. We only expect there to be one ``Transformer`` instance
    which should be instantiated from the main entrypoint function.
    """

    def __init__(self, result: LintResult):
        """Initialize a Transformer instance."""
        # TODO: Make these yaml_* options configurable
        self.yaml_explicit_start = True
        self.yaml_explicit_end = False
        self.yaml_indent_sequences = True
        self.yaml_preferred_quote = '"'
        # yaml.width defaults to 80 which wraps longer lines in tests
        self.yaml_width = 120

        self._yaml: Optional[YAML] = None

        self.matches: List[MatchError] = result.matches
        self.files: Set[Lintable] = result.files

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
              tasks:
              - name: task

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
                tasks:
                  - name: task

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
              tasks:
                - name: task
        """
        if self._yaml is not None:
            return self._yaml

        # ruamel.yaml rt=round trip (preserves comments while allowing for modification)
        yaml = YAML(typ="rt")

        # NB: ruamel.yaml does not have typehints, so mypy complains about everything here.

        # Ansible uses PyYAML which only supports YAML 1.1. ruamel.yaml defaults to 1.2.
        # So, we have to make sure we dump yaml files using YAML 1.1.
        # We can relax the version requirement once ansible uses a version of PyYAML
        # that includes this PR: https://github.com/yaml/pyyaml/pull/555
        yaml.version = (1, 1)  # type: ignore[assignment]
        # Sadly, this means all YAML files will be prefixed with "%YAML 1.1\n" on dump
        # We'll have to drop that using a transform so people don't yell too much.

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

        # ignore invalid preferred_quote setting
        if self.yaml_preferred_quote in ['"', "'"]:
            FormattedEmitter.preferred_quote = self.yaml_preferred_quote

        if self.yaml_indent_sequences or self.yaml_preferred_quote == '"':
            # For root-level sequences, FormattedEmitter overrides sequence_indent
            # and sequence_dash_offset to prevent root-level indents.
            yaml.Emitter = FormattedEmitter

        self._yaml = yaml
        return yaml

    def run(self) -> None:
        """For each file, read it, execute transforms on it, then write it."""
