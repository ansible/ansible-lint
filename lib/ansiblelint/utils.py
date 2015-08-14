# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import glob
import imp
import ansible.utils
from ansible.playbook.task import Task
import ansible.constants as C
from ansible.module_utils.splitter import split_args
import yaml
from yaml.composer import Composer
from yaml.constructor import Constructor

LINE_NUMBER_KEY = '__line__'


def load_plugins(directory):
    result = []
    fh = None

    for pluginfile in glob.glob(os.path.join(directory, '[A-Za-z]*.py')):

        pluginname = os.path.basename(pluginfile.replace('.py', ''))
        try:
            fh, filename, desc = imp.find_module(pluginname, [directory])
            mod = imp.load_module(pluginname, fh, filename, desc)
            obj = getattr(mod, pluginname)()
            result.append(obj)
        finally:
            if fh:
                fh.close()
    return result


def tokenize(line):
    result = list()
    tokens = line.lstrip().split(" ")
    if tokens[0] == '-':
        tokens = tokens[1:]
    if tokens[0] == 'action:' or tokens[0] == 'local_action:':
        tokens = tokens[1:]
    command = tokens[0].replace(":", "")

    args = list()
    kwargs = dict()
    for arg in tokens[1:]:
        if "=" in arg:
            kv = arg.split("=", 1)
            kwargs[kv[0]] = kv[1]
        else:
            args.append(arg)
    return (command, args, kwargs)


def _playbook_items(pb_data):
    if isinstance(pb_data, dict):
        return pb_data.items()
    elif not pb_data:
        return []
    else:
        return [item for play in pb_data for item in play.items()]


def find_children(playbook):
    if not os.path.exists(playbook[0]):
        return []
    results = []
    basedir = os.path.dirname(playbook[0])
    pb_data = ansible.utils.parse_yaml_from_file(playbook[0])
    items = _playbook_items(pb_data)
    for item in items:
        for child in play_children(basedir, item, playbook[1]):
            if "$" in child['path'] or "{{" in child['path']:
                continue
            valid_tokens = list()
            for token in split_args(child['path']):
                if '=' in token:
                    break
                valid_tokens.append(token)
            path = ' '.join(valid_tokens)
            results.append({
                'path': ansible.utils.path_dwim(basedir, path),
                'type': child['type']
            })
    return results


def play_children(basedir, item, parent_type):
    delegate_map = {
        'tasks': _taskshandlers_children,
        'pre_tasks': _taskshandlers_children,
        'post_tasks': _taskshandlers_children,
        'include': _include_children,
        'roles': _roles_children,
        'dependencies': _roles_children,
        'handlers': _taskshandlers_children,
    }
    (k, v) = item
    if k in delegate_map:
        if v:
            return delegate_map[k](basedir, k, v, parent_type)
    return []


def _include_children(basedir, k, v, parent_type):
    return [{'path': ansible.utils.path_dwim(basedir, v), 'type': parent_type}]


def _taskshandlers_children(basedir, k, v, parent_type):
    return [{'path': ansible.utils.path_dwim(basedir, th['include']),
             'type': 'tasks'}
            for th in v if 'include' in th]


def _roles_children(basedir, k, v, parent_type):
    results = []
    for role in v:
        if isinstance(role, dict):
            results.extend(_look_for_role_files(basedir, role['role']))
        else:
            results.extend(_look_for_role_files(basedir, role))
    return results


def _rolepath(basedir, role):
    role_path = None

    possible_paths = [
        # if included from a playbook
        ansible.utils.path_dwim(basedir, os.path.join('roles', role)),
        ansible.utils.path_dwim(basedir, role),
        # if included from roles/[role]/meta/main.yml
        ansible.utils.path_dwim(
            basedir, os.path.join('..', '..', '..', 'roles', role)
        ),
        ansible.utils.path_dwim(basedir,
                                os.path.join('..', '..', role))
    ]

    if C.DEFAULT_ROLES_PATH:
        search_locations = C.DEFAULT_ROLES_PATH.split(os.pathsep)
        for loc in search_locations:
            loc = os.path.expanduser(loc)
            possible_paths.append(ansible.utils.path_dwim(loc, role))

    for path_option in possible_paths:
        if os.path.isdir(path_option):
            role_path = path_option
            break

    return role_path


def _look_for_role_files(basedir, role):
    role_path = _rolepath(basedir, role)
    if not role_path:
        return []

    results = []

    for th in ['tasks', 'handlers', 'meta']:
        for ext in ('.yml', '.yaml'):
            thpath = os.path.join(role_path, th, 'main' + ext)
            if os.path.exists(thpath):
                results.append({'path': thpath, 'type': th})
                break
    return results


def rolename(filepath):
    idx = filepath.find('roles/')
    if idx < 0:
        return ''
    role = filepath[idx+6:]
    role = role[:role.find('/')]
    return role


def _kv_to_dict(v):
    (command, args, kwargs) = tokenize(v)
    return (dict(module=command, module_arguments=args, **kwargs))


def normalize_task(task):
    ''' ensures that all tasks have an action key
        and that string values are converted to python objects '''

    result = dict()
    for (k, v) in task.items():
        if k in Task.VALID_KEYS or k.startswith('with_'):
            if k == 'local_action' or k == 'action':
                if not isinstance(v, dict):
                    v = _kv_to_dict(v)
                v['module_arguments'] = v.get('module_arguments', list())
                result['action'] = v
            else:
                result[k] = v
        else:
            if isinstance(v, basestring):
                v = _kv_to_dict(k + ' ' + v)
            elif not v:
                v = dict(module=k)
            else:
                if isinstance(v, dict):
                    v.update(dict(module=k))
                else:
                    if k == '__line__':
                        # Keep the line number stored
                        result[k] = v
                        continue

                    else:
                        # Should not get here!
                        print "Was not expecting value %s of type %s for key %s" % (str(v), type(v), k)
                        print "Task: %s" % str(task)
                        exit(1)
            v['module_arguments'] = v.get('module_arguments', list())
            result['action'] = v
    return result


def task_to_str(task):
    name = task.get("name")
    if name:
        return name
    action = task.get("action")
    args = " ".join(["k=v" for (k, v) in action.items() if k != "module_arguments"] +
                    action.get("module_arguments"))
    return "{0} {1}".format(action["module"], args)


def get_action_tasks(yaml, file):
    tasks = list()
    if file['type'] in ['tasks', 'handlers']:
        tasks = yaml
    else:
        for block in yaml:
            for section in ['tasks', 'handlers', 'pre_tasks', 'post_tasks']:
                if section in block:
                    block_tasks = block.get(section) or []
                    tasks.extend(block_tasks)
    return [normalize_task(task) for task in tasks
            if 'include' not in task.keys()]


def parse_yaml_linenumbers(data):
    """Parses yaml as ansible.utils.parse_yaml but with linenumbers.

    The line numbers are stored in each node's LINE_NUMBER_KEY key"""
    loader = yaml.Loader(data)

    def compose_node(parent, index):
        # the line number where the previous token has ended (plus empty lines)
        line = loader.line
        node = Composer.compose_node(loader, parent, index)
        node.__line__ = line + 1
        return node

    def construct_mapping(node, deep=False):
        mapping = Constructor.construct_mapping(loader, node, deep=deep)
        mapping[LINE_NUMBER_KEY] = node.__line__
        return mapping

    loader.compose_node = compose_node
    loader.construct_mapping = construct_mapping
    data = loader.get_single_data()
    return data
