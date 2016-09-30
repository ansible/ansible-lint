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

import glob
import imp
import os

import ansible.constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.splitter import split_args
import yaml
from yaml.composer import Composer
from yaml.constructor import Constructor

try:
    from ansible.utils import parse_yaml_from_file
    from ansible.utils import path_dwim
    from ansible.utils.template import template as ansible_template
    from ansible.utils import module_finder
    module_loader = module_finder
    ANSIBLE_VERSION = 1
except ImportError:
    from ansible.parsing.dataloader import DataLoader
    from ansible.template import Templar
    from ansible.parsing.mod_args import ModuleArgsParser
    from ansible.plugins import module_loader
    from ansible.errors import AnsibleParserError
    ANSIBLE_VERSION = 2

    def parse_yaml_from_file(filepath):
        dl = DataLoader()
        return dl.load_from_file(filepath)

    def path_dwim(basedir, given):
        dl = DataLoader()
        dl.set_basedir(basedir)
        return dl.path_dwim(given)

    def ansible_template(basedir, varname, templatevars, **kwargs):
        dl = DataLoader()
        dl.set_basedir(basedir)
        templar = Templar(dl, variables=templatevars)
        return templar.template(varname, **kwargs)

LINE_NUMBER_KEY = '__line__'
FILENAME_KEY = '__file__'

VALID_KEYS = [
    'name', 'action', 'when', 'async', 'poll', 'notify',
    'first_available_file', 'include', 'tags', 'register', 'ignore_errors',
    'delegate_to', 'local_action', 'transport', 'remote_user', 'sudo', 'sudo_user',
    'sudo_pass', 'when', 'connection', 'environment', 'args',
    'any_errors_fatal', 'changed_when', 'failed_when', 'always_run', 'delay', 'retries', 'until',
    'su', 'su_user', 'su_pass', 'no_log', 'run_once',
    'become', 'become_user', 'become_method', FILENAME_KEY,
]

BLOCK_NAME_TO_ACTION_TYPE_MAP = {
    'tasks': 'task',
    'handlers': 'handler',
    'pre_tasks': 'task',
    'post_tasks': 'task',
    'block': 'meta',
    'rescue': 'meta',
    'always': 'meta',
}


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
    tokens = line.lstrip().split(" ")
    if tokens[0] == '-':
        tokens = tokens[1:]
    if tokens[0] == 'action:' or tokens[0] == 'local_action:':
        tokens = tokens[1:]
    command = tokens[0].replace(":", "")

    args = list()
    kwargs = dict()
    nonkvfound = False
    for arg in tokens[1:]:
        if "=" in arg and not nonkvfound:
            kv = arg.split("=", 1)
            kwargs[kv[0]] = kv[1]
        else:
            nonkvfound = True
            args.append(arg)
    return (command, args, kwargs)


def _playbook_items(pb_data):
    if isinstance(pb_data, dict):
        return pb_data.items()
    elif not pb_data:
        return []
    else:
        return [item for play in pb_data for item in play.items()]


def find_children(playbook, playbook_dir):
    if not os.path.exists(playbook[0]):
        return []
    if playbook[1] == 'role':
        playbook_ds = {'roles': [{'role': playbook[0]}]}
    else:
        try:
            playbook_ds = parse_yaml_from_file(playbook[0])
        except AnsibleError, e:
            raise SystemExit(str(e))
    results = []
    basedir = os.path.dirname(playbook[0])
    items = _playbook_items(playbook_ds)
    for item in items:
        for child in play_children(basedir, item, playbook[1], playbook_dir):
            if "$" in child['path'] or "{{" in child['path']:
                continue
            valid_tokens = list()
            for token in split_args(child['path']):
                if '=' in token:
                    break
                valid_tokens.append(token)
            path = ' '.join(valid_tokens)
            results.append({
                'path': path_dwim(basedir, path),
                'type': child['type']
            })
    return results


def template(basedir, value, vars, fail_on_undefined=False, **kwargs):
    try:
        value = ansible_template(os.path.abspath(basedir), value, vars,
                                 **dict(kwargs, fail_on_undefined=fail_on_undefined))
        # Hack to skip the following exception when using to_json filter on a variable.
        # I guess the filter doesn't like empty vars...
    except (AnsibleError, ValueError):
        # templating failed, so just keep value as is.
        pass
    return value


def play_children(basedir, item, parent_type, playbook_dir):
    delegate_map = {
        'tasks': _taskshandlers_children,
        'pre_tasks': _taskshandlers_children,
        'post_tasks': _taskshandlers_children,
        'block': _taskshandlers_children,
        'include': _include_children,
        'roles': _roles_children,
        'dependencies': _roles_children,
        'handlers': _taskshandlers_children,
    }
    (k, v) = item
    play_library = os.path.join(os.path.abspath(basedir), 'library')
    _load_library_if_exists(play_library)

    if k in delegate_map:
        if v:
            v = template(os.path.abspath(basedir),
                         v,
                         dict(playbook_dir=os.path.abspath(basedir)),
                         fail_on_undefined=False)
            return delegate_map[k](basedir, k, v, parent_type)
    return []


def _include_children(basedir, k, v, parent_type):
    # handle include: filename.yml tags=blah
    (command, args, kwargs) = tokenize("{0}: {1}".format(k, v))

    result = path_dwim(basedir, args[0])
    if not os.path.exists(result) and not basedir.endswith('tasks'):
        result = path_dwim(os.path.join(basedir, '..', 'tasks'), v)
    return [{'path': result, 'type': parent_type}]


def _taskshandlers_children(basedir, k, v, parent_type):
    results = []
    for th in v:
        if 'include' in th:
            results.append({
                'path': path_dwim(basedir, th['include']),
                'type': 'tasks'
            })
        elif 'block' in th:
            results.extend(_taskshandlers_children(basedir, k, th['block'], parent_type))
            if 'rescue' in th:
                results.extend(_taskshandlers_children(basedir, k, th['rescue'], parent_type))
            if 'always' in th:
                results.extend(_taskshandlers_children(basedir, k, th['always'], parent_type))

    return results


def _roles_children(basedir, k, v, parent_type):
    results = []
    for role in v:
        if isinstance(role, dict):
            if 'role' in role or 'name' in role:
                if 'tags' not in role or 'skip_ansible_lint' not in role['tags']:
                    results.extend(_look_for_role_files(basedir,
                                                        role.get('role', role.get('name'))))
            else:
                raise SystemExit('role dict {0} does not contain a "role" '
                                 'or "name" key'.format(role))
        else:
            results.extend(_look_for_role_files(basedir, role))
    return results


def _load_library_if_exists(path):
    if os.path.exists(path):
        module_loader.add_directory(path)


def _rolepath(basedir, role):
    role_path = None

    possible_paths = [
        # if included from a playbook
        path_dwim(basedir, os.path.join('roles', role)),
        path_dwim(basedir, role),
        # if included from roles/[role]/meta/main.yml
        path_dwim(
            basedir, os.path.join('..', '..', '..', 'roles', role)
        ),
        path_dwim(basedir, os.path.join('..', '..', role))
    ]

    if C.DEFAULT_ROLES_PATH:
        search_locations = C.DEFAULT_ROLES_PATH
        if isinstance(search_locations, basestring):
            search_locations = search_locations.split(os.pathsep)
        for loc in search_locations:
            loc = os.path.expanduser(loc)
            possible_paths.append(path_dwim(loc, role))

    for path_option in possible_paths:
        if os.path.isdir(path_option):
            role_path = path_option
            break

    if role_path:
        _load_library_if_exists(os.path.join(role_path, 'library'))

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
    return (dict(__ansible_module__=command, __ansible_arguments__=args, **kwargs))


def normalize_task_v2(task):
    '''Ensures tasks have an action key and strings are converted to python objects'''

    result = dict()
    mod_arg_parser = ModuleArgsParser(task)
    try:
        action, arguments, result['delegate_to'] = mod_arg_parser.parse()
    except AnsibleParserError as e:
        try:
            task_info = "%s:%s" % (task[FILENAME_KEY], task[LINE_NUMBER_KEY])
            del task[FILENAME_KEY]
            del task[LINE_NUMBER_KEY]
        except KeyError:
            task_info = "Unknown"
        try:
            import pprint
            pp = pprint.PrettyPrinter(indent=2)
            task_pprint = pp.pformat(task)
        except ImportError:
            task_pprint = task
        raise SystemExit("Couldn't parse task at %s (%s)\n%s" % (task_info, e.message, task_pprint))

    # denormalize shell -> command conversion
    if '_uses_shell' in arguments:
        action = 'shell'
        del(arguments['_uses_shell'])

    for (k, v) in list(task.items()):
        if k in ('action', 'local_action', 'args', 'delegate_to') or k == action:
            # we don't want to re-assign these values, which were
            # determined by the ModuleArgsParser() above
            continue
        else:
            result[k] = v

    result['action'] = dict(__ansible_module__=action)

    if '_raw_params' in arguments:
        result['action']['__ansible_arguments__'] = arguments['_raw_params'].split()
        del(arguments['_raw_params'])
    else:
        result['action']['__ansible_arguments__'] = list()
    result['action'].update(arguments)
    return result


def normalize_task_v1(task):
    result = dict()
    for (k, v) in task.items():
        if k in VALID_KEYS or k.startswith('with_'):
            if k == 'local_action' or k == 'action':
                if not isinstance(v, dict):
                    v = _kv_to_dict(v)
                v['__ansible_arguments__'] = v.get('__ansible_arguments__', list())
                result['action'] = v
            else:
                result[k] = v
        else:
            if isinstance(v, basestring):
                v = _kv_to_dict(k + ' ' + v)
            elif not v:
                v = dict(__ansible_module__=k)
            else:
                if isinstance(v, dict):
                    v.update(dict(__ansible_module__=k))
                else:
                    if k == '__line__':
                        # Keep the line number stored
                        result[k] = v
                        continue

                    else:
                        # Tasks that include playbooks (rather than task files)
                        # can get here
                        # https://github.com/willthames/ansible-lint/issues/138
                        raise RuntimeError("Was not expecting value %s of type %s for key %s\n"
                                           "Task: %s. Check the syntax of your playbook using "
                                           "ansible-playbook --syntax-check" %
                                           (str(v), type(v), k, str(task)))
            v['__ansible_arguments__'] = v.get('__ansible_arguments__', list())
            result['action'] = v
    if 'module' in result['action']:
        # this happens when a task uses
        # local_action:
        #   module: ec2
        #   etc...
        result['action']['__ansible_module__'] = result['action']['module']
        del(result['action']['module'])
    if 'args' in result:
        result['action'].update(result.get('args'))
        del(result['args'])
    return result


def normalize_task(task, filename):
    ansible_action_type = task.get('__ansible_action_type__', 'task')
    if '__ansible_action_type__' in task:
        del(task['__ansible_action_type__'])
    if ANSIBLE_VERSION < 2:
        task = normalize_task_v1(task)
    else:
        task = normalize_task_v2(task)
    task[FILENAME_KEY] = filename
    task['__ansible_action_type__'] = ansible_action_type
    return task


def task_to_str(task):
    name = task.get("name")
    if name:
        return name
    action = task.get("action")
    args = " " .join(["{0}={1}".format(k, v) for (k, v) in action.items()
                     if k not in ["__ansible_module__", "__ansible_arguments__"]] +
                     action.get("__ansible_arguments__"))
    return "{0} {1}".format(action["__ansible_module__"], args)


def extract_from_list(blocks, candidates):
    results = list()
    for block in blocks:
        for candidate in candidates:
            if isinstance(block, dict) and candidate in block:
                if isinstance(block[candidate], list):
                    results.extend(add_action_type(block[candidate], candidate))
                elif block[candidate] is not None:
                    raise RuntimeError(
                        "Key '%s' defined, but bad value: '%s'" %
                        (candidate, str(block[candidate])))
    return results


def add_action_type(actions, action_type):
    results = list()
    for action in actions:
        action['__ansible_action_type__'] = BLOCK_NAME_TO_ACTION_TYPE_MAP[action_type]
        results.append(action)
    return results


def get_action_tasks(yaml, file):
    tasks = list()
    if file['type'] in ['tasks', 'handlers']:
        tasks = add_action_type(yaml, file['type'])
    else:
        tasks.extend(extract_from_list(yaml, ['tasks', 'handlers', 'pre_tasks', 'post_tasks']))

    # Add sub-elements of block/rescue/always to tasks list
    tasks.extend(extract_from_list(tasks, ['block', 'rescue', 'always']))
    # Remove block/rescue/always elements from tasks list
    block_rescue_always = ('block', 'rescue', 'always')
    tasks[:] = [task for task in tasks if all(k not in task for k in block_rescue_always)]

    return [task for task in tasks if 'include' not in task.keys()]


def get_normalized_tasks(yaml, file):
    tasks = get_action_tasks(yaml, file)
    return [normalize_task(task, file['path']) for task in tasks]


def parse_yaml_linenumbers(data, filename):
    """Parses yaml as ansible.utils.parse_yaml but with linenumbers.

    The line numbers are stored in each node's LINE_NUMBER_KEY key.
    """

    def compose_node(parent, index):
        # the line number where the previous token has ended (plus empty lines)
        line = loader.line
        node = Composer.compose_node(loader, parent, index)
        node.__line__ = line + 1
        return node

    def construct_mapping(node, deep=False):
        mapping = Constructor.construct_mapping(loader, node, deep=deep)
        mapping[LINE_NUMBER_KEY] = node.__line__
        mapping[FILENAME_KEY] = filename
        return mapping

    try:
        loader = yaml.Loader(data)
        loader.compose_node = compose_node
        loader.construct_mapping = construct_mapping
        data = loader.get_single_data()
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
        raise SystemExit("Failed to parse YAML in %s: %s" % (filename, str(e)))
    return data
