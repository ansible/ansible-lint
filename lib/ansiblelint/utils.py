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
import shlex
from ansible.playbook.task import Task


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
            if kv[0] == 'args':
                kv[0] = 'task_args'
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
            path = shlex.split(child['path'])[0]  # strip tags=smsng
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
    if os.path.isabs(role):
        return role
    # if included from a playbook
    pbrolepath = ansible.utils.path_dwim(basedir, os.path.join('roles', role))
    if os.path.exists(pbrolepath):
        return pbrolepath
    # if included from roles/meta/main.yml
    gpdir = os.path.normpath(os.path.join(basedir, '..', '..'))
    if os.path.basename(gpdir) == 'roles':
        rolepath = os.path.join(gpdir, role)
        return rolepath
    return basedir


def _look_for_role_files(basedir, role):
    results = []
    for th in ['tasks', 'handlers', 'meta']:
        thpath = os.path.join(_rolepath(basedir, role), th, 'main.yml')
        if os.path.exists(thpath):
            results.append({'path': thpath, 'type': th})
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
    return (dict(module=command, args=args, **kwargs))


def normalize_task(task):
    ''' ensures that all tasks have an action key
        and that string values are converted to python objects '''

    result = dict()
    for (k, v) in task.items():
        if k in Task.VALID_KEYS or k.startswith('with_'):
            if k == 'local_action' or k == 'action':
                if not isinstance(v, dict):
                    v = _kv_to_dict(v)
                v['args'] = v.get('args', list())
                result['action'] = v
            else:
                result[k] = v
        else:
            if isinstance(v, str):
                v = _kv_to_dict(k + ' ' + v)
            else:
                if isinstance(v, dict):
                    v.update(dict(module=k))
                else:
                    # Should not get here!
                    assert False
            v['args'] = v.get('args', list())
            result['action'] = v
    return result


def task_to_str(task):
    name = task.get("name")
    if name:
        return name
    action = task.get("action")
    args = " ".join(["k=v" for (k, v) in action.items() if k != "args"] +
                    action["args"])
    return "{0} {1}".format(action["module"], args)


def get_action_tasks(yaml, file):
    tasks = list()
    if file['type'] in ['tasks', 'handlers']:
        tasks = yaml
    else:
        for block in yaml:
            for section in ['tasks', 'handlers', 'pre_tasks', 'post_tasks']:
                if section in block:
                    tasks.extend(block.get(section))
    return [normalize_task(task) for task in tasks
            if 'include' not in task.keys()]
