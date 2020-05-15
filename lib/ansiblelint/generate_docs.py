"""Utils to generate rule table .rst documentation."""
import logging
from functools import reduce


DOC_HEADER = """
.. _lint_default_rules:

Default Rules
=============

.. contents:: Topics

The table below shows the default rules used by Ansible Lint to evaluate playbooks and roles:

"""

_logger = logging.getLogger(__name__)


def make_table(grid):
    """Convert a grid into a space delimited table."""
    cell_width = 2 + max(reduce(lambda x, y: x + y,
                                [[len(item) for item in row] for row in grid], []))
    num_cols = len(grid[0])
    block = DOC_HEADER
    header = True
    for row in grid:
        if header:
            block = block + num_cols * ((cell_width) * '=' + ' ') + '\n'

        block = block + ''.join([normalize_cell(x, cell_width + 1)
                                 for x in row]) + '\n'
        if header:
            block = block + num_cols * ((cell_width) * '=' + ' ') + '\n'
        header = False
    block = block + num_cols * ((cell_width) * '=' + ' ') + '\n'
    # remove trailing whitelines from block
    block = '\n'.join(line.rstrip() for line in block.splitlines())
    return block


def normalize_cell(string, length):
    """Format string to a fixed length."""
    return string + ((length - len(string)) * ' ')


def rules_as_rst(rules):
    """Return RST documentation for a list of rules."""
    id_link = ('`E{} <https://github.com/ansible/ansible-lint/blob/'
               'master/lib/ansiblelint/rules/{}.py>`_')

    grid = [['ID', 'Version Added', 'Sample Message', 'Description']]

    for d in rules:
        if not hasattr(d, 'id'):
            _logger.warning(
                "Rule %s skipped from being documented as it does not have an `id` attribute.",
                d.__class__.__name__)
            continue

        if d.id.endswith('01'):
            if not d.id.endswith('101'):
                grid.append(['', '', '', ''])
            grid.append([
                '**E{}xx - {}**'.format(
                    d.id[-3:-2],
                    d.tags[0]),
                '',
                '',
                '',
            ])
        id_text = id_link.format(d.id, d.__class__.__name__)
        grid.append([id_text, d.version_added, d.shortdesc, d.description])

    return make_table(grid)
