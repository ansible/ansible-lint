"""Transformer implementation."""
import logging
from typing import List, Optional, Set

# Module 'ruamel.yaml' does not explicitly export attribute 'YAML'; implicit reexport disabled
# To make the type checkers happy, we import from ruamel.yaml.main instead.
from ruamel.yaml.main import YAML

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.runner import LintResult
from ansiblelint.yaml_utils import FormattedEmitter

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
