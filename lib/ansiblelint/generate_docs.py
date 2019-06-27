'''Script to generate rule table .rst documentation.'''

import os
import importlib
from inspect import getmembers, ismodule, isclass
import rules
from ansiblelint import AnsibleLintRule
from functools import reduce

DOC_HEADER = """
.. _lint_default_rules:

Default Rules
=============

.. contents:: Topics

The table below shows the the default rules used by Ansible Lint to evaluate playbooks and roles:

"""


def main():
    id_link = ('`E{} <https://github.com/ansible/ansible-lint/blob/'
               'master/lib/ansiblelint/rules/{}.py>`_')

    import_all_rules()
    all_rules = get_serialized_rules()

    grid = [['ID', 'Version Added', 'Sample Message', 'Description']]
    for d in all_rules:
        if d['id'].endswith('01'):
            if not d['id'].endswith('101'):
                grid.append(['', '', '', ''])
            grid.append([
                '**E{}xx - {}**'.format(d['id'][-3:-2], d['first_tag']),
                '',
                '',
                # '**{}**'.format(d['first_tag']),
                '',
            ])
        id_text = id_link.format(d['id'], d['classname'])
        grid.append([id_text, d['version_added'], d['shortdesc'], d['description']])

    filename = '../../docs/docsite/rst/rules/default_rules.rst'
    with open(filename, 'w') as file:
        file.write(make_table(grid))
        print('{} file written'.format(filename))


def import_all_rules():
    for module in list(os.walk('rules'))[0][2]:
        if module == '__init__.py' or module[-3:] != '.py':
            continue
        module = 'rules.{}'.format(module[:-3])
        importlib.import_module(module)


def get_serialized_rules():
    mod_list = [m[1] for m in getmembers(rules) if ismodule(m[1])]
    class_list = []
    for mod in mod_list:
        class_temp = [m[1] for m in getmembers(mod) if isclass(m[1])]
        class_temp = [c for c in class_temp if c is not AnsibleLintRule]
        class_list.extend(class_temp)

    all_rules = []
    for c in class_list:
        d = {
            'id': c.id,
            'shortdesc': c.shortdesc,
            'description': c.description,
            'first_tag': c.tags[0],
            'classname': c.__name__,
            'version_added': c.version_added,
        }
        all_rules.append(d)
    all_rules = sorted(all_rules, key=lambda k: k['id'])
    return all_rules


def make_table(grid):
    cell_width = 2 + max(reduce(lambda x, y: x+y,
                                [[len(item) for item in row] for row in grid], []))
    num_cols = len(grid[0])
    block = DOC_HEADER
    header = True
    for row in grid:
        if header:
            block = block + num_cols*((cell_width)*'=' + ' ') + '\n'

        block = block + ''.join([normalize_cell(x, cell_width+1)
                                 for x in row]) + '\n'
        if header:
            block = block + num_cols*((cell_width)*'=' + ' ') + '\n'
        header = False
    block = block + num_cols*((cell_width)*'=' + ' ') + '\n'
    return block


def normalize_cell(string, length):
    return string + ((length - len(string)) * ' ')


if __name__ == '__main__':
    main()
