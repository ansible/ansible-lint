"""Utils to generate rule table .rst documentation."""
import logging
from typing import Iterable

from rich import box
from rich.console import render_group
from rich.markdown import Markdown
from rich.table import Table

from ansiblelint.rules import RulesCollection

DOC_HEADER = """
.. _lint_default_rules:

Default Rules
=============

.. contents::
   :local:

Below you can see the list of default rules Ansible Lint use to evaluate playbooks and roles:

"""

_logger = logging.getLogger(__name__)


def rules_as_str(rules: RulesCollection) -> str:
    """Return rules as string."""
    return str(rules)


def rules_as_rst(rules: RulesCollection) -> str:
    """Return RST documentation for a list of rules."""
    r = DOC_HEADER

    for d in rules:

        title = f"{d.id}"

        description = d.description
        if d.link:
            description += " `(more) <%s>`__" % d.link

        r += f"\n\n.. _{d.id}:\n\n{title}\n{'*' * len(title)}\n\n{d.shortdesc}\n\n{description}"

    return r


@render_group()
def rules_as_rich(rules: RulesCollection) -> Iterable[Table]:
    """Print documentation for a list of rules, returns empty string."""
    width = max(16, *[len(rule.id) for rule in rules])
    for rule in rules:
        table = Table(show_header=True, header_style="title", box=box.MINIMAL)
        table.add_column(rule.id, style="dim", width=width)
        table.add_column(Markdown(rule.shortdesc))
        description = rule.description
        if rule.link:
            description += " [(more)](%s)" % rule.link
        table.add_row("description", Markdown(description))
        if rule.version_added:
            table.add_row("version_added", rule.version_added)
        if rule.tags:
            table.add_row("tags", ", ".join(rule.tags))
        if rule.severity:
            table.add_row("severity", rule.severity)
        yield table
