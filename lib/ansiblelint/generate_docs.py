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


def rules_as_rst(rules: RulesCollection) -> str:
    """Return RST documentation for a list of rules."""
    r = DOC_HEADER

    for d in rules:
        if not hasattr(d, 'id'):
            _logger.warning(
                "Rule %s skipped from being documented as it does not have an `id` attribute.",
                d.__class__.__name__)
            continue

        if d.id.endswith('01'):

            section = '{} Rules ({}xx)'.format(
                    d.tags[0].title(),
                    d.id[-3:-2])
            r += f'\n\n{section}\n{ "-" * len(section) }'

        title = f"{d.id}: {d.shortdesc}"
        r += f"\n\n.. _{d.id}:\n\n{title}\n{'*' * len(title)}\n\n{d.description}"

    return r


@render_group()
def rules_as_rich(rules: RulesCollection) -> Iterable[Table]:
    """Print documentation for a list of rules, returns empty string."""
    for rule in rules:
        table = Table(show_header=True, header_style="title", box=box.MINIMAL)
        table.add_column(rule.id, style="dim", width=16)
        table.add_column(Markdown(rule.shortdesc))
        table.add_row("description", Markdown(rule.description))
        if rule.version_added:
            table.add_row("version_added", rule.version_added)
        if rule.tags:
            table.add_row("tags", ", ".join(rule.tags))
        if rule.severity:
            table.add_row("severity", rule.severity)
        yield table
