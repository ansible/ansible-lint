"""Utils to generate rule table .rst documentation."""
import logging

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
