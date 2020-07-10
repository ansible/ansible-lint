#! /usr/bin/env python3
# Requires Python 3.6+
"""Sphinx extension for generating the rules table document."""

from contextlib import suppress
from pathlib import Path
from typing import Any, Dict

from sphinx.application import Sphinx

from ansiblelint import __version__
from ansiblelint.constants import DEFAULT_RULESDIR
from ansiblelint.generate_docs import rules_as_rst
from ansiblelint.rules import RulesCollection

DEFAULT_RULES_RST = (Path(__file__).parent / 'default_rules.rst').resolve()


def _generate_default_rules(app: Sphinx) -> None:
    """Generate the default rules table RST file."""
    default_rules = RulesCollection([DEFAULT_RULESDIR])
    rst_rules_table = rules_as_rst(default_rules)
    DEFAULT_RULES_RST.write_text(rst_rules_table)


def _cleanup_default_rules(app: Sphinx, exception: Exception) -> None:
    """Remove the rules table RST file."""
    with suppress(FileNotFoundError):
        DEFAULT_RULES_RST.unlink()


def setup(app: Sphinx) -> Dict[str, Any]:
    """Initialize the Sphinx extension."""
    app.connect('builder-inited', _generate_default_rules)
    app.connect('build-finished', _cleanup_default_rules)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
        'version': __version__,
    }
