#! /usr/bin/env python3
# Requires Python 3.6+
"""Sphinx extension for generating the rules table document."""

from typing import Dict, List, Union

from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import nested_parse_with_titles, nodes

# isort: split

from docutils import statemachine

from ansiblelint import __version__
from ansiblelint.constants import DEFAULT_RULESDIR
from ansiblelint.generate_docs import rules_as_md
from ansiblelint.rules import RulesCollection


def _nodes_from_md(
    state: statemachine.State,
    md_source: str,
) -> List[nodes.Node]:
    """Turn an MD string into a list of nodes.

    These nodes can be used in the document.
    """
    node = nodes.Element()
    node.document = state.document
    nested_parse_with_titles(
        state=state,
        content=statemachine.ViewList(
            statemachine.string2lines(md_source),
            source="[ansible-lint autogenerated]",
        ),
        node=node,
    )
    return node.children


class AnsibleLintDefaultRulesDirective(SphinxDirective):
    """Directive ``ansible-lint-default-rules-list`` definition."""

    has_content = False

    def run(self) -> List[nodes.Node]:
        """Generate a node tree in place of the directive."""
        self.env.note_reread()  # rebuild the current doc unconditionally

        default_rules = RulesCollection([DEFAULT_RULESDIR])
        md_rules_table = rules_as_md(default_rules)

        return _nodes_from_md(state=self.state, md_source=md_rules_table)


def setup(app: Sphinx) -> Dict[str, Union[bool, str]]:
    """Initialize the Sphinx extension."""
    app.add_directive(
        "ansible-lint-default-rules-list",
        AnsibleLintDefaultRulesDirective,
    )

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": __version__,
    }
