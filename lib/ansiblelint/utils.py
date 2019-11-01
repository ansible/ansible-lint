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

from collections import OrderedDict
import glob
import imp
from itertools import product
import os
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path
import subprocess


import six
from ansible import constants
from ansible.errors import AnsibleError

try:
    # Try to import the Ansible 2 module first, it's the future-proof one
    from ansible.parsing.splitter import split_args

except ImportError:
    # Fallback on the Ansible 1.9 module
    from ansible.module_utils.splitter import split_args

import yaml
from yaml.composer import Composer
from yaml.constructor import Constructor
import ruamel.yaml

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
    from ansible.parsing.yaml.constructor import AnsibleConstructor
    from ansible.parsing.yaml.loader import AnsibleLoader
    from ansible.parsing.yaml.objects import AnsibleSequence
    from ansible.errors import AnsibleParserError
    ANSIBLE_VERSION = 2

    # ansible-lint doesn't need/want to know about encrypted secrets, but it needs
    # Ansible 2.3+ allows encrypted secrets within yaml files, so we pass a string
    # as the password to enable such yaml files to be opened and parsed successfully.
    DEFAULT_VAULT_PASSWORD = 'x'

    def parse_yaml_from_file(filepath):
        dl = DataLoader()
        if hasattr(dl, 'set_vault_password'):
            dl.set_vault_password(DEFAULT_VAULT_PASSWORD)
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
    try:
        from ansible.plugins import module_loader
    except ImportError:
        from ansible.plugins.loader import module_loader

LINE_NUMBER_KEY = '__line__'
FILENAME_KEY = '__file__'

VALID_KEYS = [
    'name', 'action', 'when', 'async', 'poll', 'notify',
    'first_available_file', 'include', 'include_tasks', 'import_tasks', 'import_playbook',
    'tags', 'register', 'ignore_errors', 'delegate_to',
    'local_action', 'transport', 'remote_user', 'sudo',
    'sudo_user', 'sudo_pass', 'when', 'connection', 'environment', 'args', 'always_run',
    'any_errors_fatal', 'changed_when', 'failed_when', 'check_mode', 'delay',
    'retries', 'until', 'su', 'su_user', 'su_pass', 'no_log', 'run_once',
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
        except AnsibleError as e:
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
        'import_playbook': _include_children,
        'roles': _roles_children,
        'dependencies': _roles_children,
        'handlers': _taskshandlers_children,
        'include_tasks': _include_children,
        'import_tasks': _include_children,
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
            append_children(th['include'], basedir, k, parent_type, results)
        elif 'include_tasks' in th:
            append_children(th['include_tasks'], basedir, k, parent_type, results)
        elif 'import_playbook' in th:
            append_children(th['import_playbook'], basedir, k, parent_type, results)
        elif 'import_tasks' in th:
            append_children(th['import_tasks'], basedir, k, parent_type, results)
        elif 'import_role' in th:
            th = normalize_task_v2(th)
            results.extend(_roles_children(basedir, k, [th['action'].get('name')], parent_type,
                                           main=th['action'].get('tasks_from', 'main')))
        elif 'include_role' in th:
            th = normalize_task_v2(th)
            results.extend(_roles_children(basedir, k, [th['action'].get('name')],
                                           parent_type,
                                           main=th['action'].get('tasks_from', 'main')))
        elif 'block' in th:
            results.extend(_taskshandlers_children(basedir, k, th['block'], parent_type))
            if 'rescue' in th:
                results.extend(_taskshandlers_children(basedir, k, th['rescue'], parent_type))
            if 'always' in th:
                results.extend(_taskshandlers_children(basedir, k, th['always'], parent_type))
    return results


def append_children(taskhandler, basedir, k, parent_type, results):
    # when taskshandlers_children is called for playbooks, the
    # actual type of the included tasks is the section containing the
    # include, e.g. tasks, pre_tasks, or handlers.
    if parent_type == 'playbook':
        playbook_section = k
    else:
        playbook_section = parent_type
    results.append({
        'path': path_dwim(basedir, taskhandler),
        'type': playbook_section
    })


def _roles_children(basedir, k, v, parent_type, main='main'):
    results = []
    for role in v:
        if isinstance(role, dict):
            if 'role' in role or 'name' in role:
                if 'tags' not in role or 'skip_ansible_lint' not in role['tags']:
                    results.extend(_look_for_role_files(basedir,
                                                        role.get('role', role.get('name')),
                                                        main=main))
            elif k != 'dependencies':
                raise SystemExit('role dict {0} does not contain a "role" '
                                 'or "name" key'.format(role))
        else:
            results.extend(_look_for_role_files(basedir, role, main=main))
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
        path_dwim(basedir, os.path.join('..', '..', role)),
    ]

    if constants.DEFAULT_ROLES_PATH:
        search_locations = constants.DEFAULT_ROLES_PATH
        if isinstance(search_locations, six.string_types):
            search_locations = search_locations.split(os.pathsep)
        for loc in search_locations:
            loc = os.path.expanduser(loc)
            possible_paths.append(path_dwim(loc, role))

    possible_paths.append(path_dwim(basedir, ''))

    for path_option in possible_paths:
        if os.path.isdir(path_option):
            role_path = path_option
            break

    if role_path:
        _load_library_if_exists(os.path.join(role_path, 'library'))

    return role_path


def _look_for_role_files(basedir, role, main='main'):
    role_path = _rolepath(basedir, role)
    if not role_path:
        return []

    results = []

    for th in ['tasks', 'handlers', 'meta']:
        current_path = os.path.join(role_path, th)
        for dir, subdirs, files in os.walk(current_path):
            for file in files:
                file_ignorecase = file.lower()
                if file_ignorecase.endswith(('.yml', '.yaml')):
                    thpath = os.path.join(dir, file)
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
        result['action']['__ansible_arguments__'] = arguments['_raw_params'].split(' ')
        del(arguments['_raw_params'])
    else:
        result['action']['__ansible_arguments__'] = list()

    if 'argv' in arguments and not result['action']['__ansible_arguments__']:
        result['action']['__ansible_arguments__'] = arguments['argv']
        del(arguments['argv'])

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
            if isinstance(v, six.string_types):
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
                        # https://github.com/ansible/ansible-lint/issues/138
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
    args = " ".join([u"{0}={1}".format(k, v) for (k, v) in action.items()
                     if k not in ["__ansible_module__", "__ansible_arguments__"]] +
                    action.get("__ansible_arguments__"))
    return u"{0} {1}".format(action["__ansible_module__"], args)


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

    return [task for task in tasks if
            set(['include', 'include_tasks',
                'import_playbook', 'import_tasks']).isdisjoint(task.keys())]


def get_normalized_tasks(yaml, file):
    tasks = get_action_tasks(yaml, file)
    res = []
    for task in tasks:
        # An empty `tags` block causes `None` to be returned if
        # the `or []` is not present - `task.get('tags', [])`
        # does not suffice.
        if 'skip_ansible_lint' in (task.get('tags') or []):
            # No need to normalize_task is we are skipping it.
            continue
        res.append(normalize_task(task, file['path']))

    return res


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
        if ANSIBLE_VERSION < 2:
            mapping = Constructor.construct_mapping(loader, node, deep=deep)
        else:
            mapping = AnsibleConstructor.construct_mapping(loader, node, deep=deep)
        if hasattr(node, '__line__'):
            mapping[LINE_NUMBER_KEY] = node.__line__
        else:
            mapping[LINE_NUMBER_KEY] = mapping._line_number
        mapping[FILENAME_KEY] = filename
        return mapping

    try:
        if ANSIBLE_VERSION < 2:
            loader = yaml.Loader(data)
        else:
            import inspect
            kwargs = {}
            if 'vault_password' in inspect.getargspec(AnsibleLoader.__init__).args:
                kwargs['vault_password'] = DEFAULT_VAULT_PASSWORD
            loader = AnsibleLoader(data, **kwargs)
        loader.compose_node = compose_node
        loader.construct_mapping = construct_mapping
        data = loader.get_single_data()
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
        raise SystemExit("Failed to parse YAML in %s: %s" % (filename, str(e)))
    return data


def get_first_cmd_arg(task):
    try:
        if 'cmd' in task['action']:
            first_cmd_arg = task['action']['cmd'].split()[0]
        else:
            first_cmd_arg = task['action']['__ansible_arguments__'][0]
    except IndexError:
        return None
    return first_cmd_arg


def append_skipped_rules(pyyaml_data, file_text, file_type):
    """Append 'skipped_rules' to individual tasks or single metadata block.

    For a file, uses 2nd parser (ruamel.yaml) to pull comments out of
    yaml subsets, check for '# noqa' skipped rules, and append any skips to the
    original parser (pyyaml) data relied on by remainder of ansible-lint.

    :param pyyaml_data: file text parsed via ansible and pyyaml.
    :param file_text: raw file text.
    :param file_type: type of file: tasks, handlers or meta.
    :returns: original pyyaml_data altered with a 'skipped_rules' list added
    to individual tasks, or added to the single metadata block.
    """

    try:
        yaml_skip = _append_skipped_rules(pyyaml_data, file_text, file_type)
    except RuntimeError as exc:
        # Notify user of skip error, do not stop, do not change exit code
        print('Error trying to append skipped rules: {!r}'.format(exc))
        return pyyaml_data
    return yaml_skip


def _append_skipped_rules(pyyaml_data, file_text, file_type):
    # parse file text using 2nd parser library
    yaml = ruamel.yaml.YAML()
    ruamel_data = yaml.load(file_text)

    if file_type == 'meta':
        pyyaml_data[0]['skipped_rules'] = _get_rule_skips_from_yaml(ruamel_data)
        return pyyaml_data

    # create list of blocks of tasks or nested tasks
    if file_type in ('tasks', 'handlers'):
        ruamel_task_blocks = ruamel_data
        pyyaml_task_blocks = pyyaml_data
    elif file_type == 'playbook':
        try:
            pyyaml_task_blocks = _get_task_blocks_from_playbook(pyyaml_data)
            ruamel_task_blocks = _get_task_blocks_from_playbook(ruamel_data)
        except (AttributeError, TypeError):
            # TODO(awcrosby): running ansible-lint on any .yml file will
            # assume it is a playbook, check needs to be added higher in the
            # call stack, and can remove this except
            return pyyaml_data
    else:
        raise RuntimeError('Unexpected file type: {}'.format(file_type))

    # get tasks from blocks of tasks
    pyyaml_tasks = _get_tasks_from_blocks(pyyaml_task_blocks)
    ruamel_tasks = _get_tasks_from_blocks(ruamel_task_blocks)

    # append skipped_rules for each task
    for ruamel_task, pyyaml_task in zip(ruamel_tasks, pyyaml_tasks):
        if pyyaml_task.get('name') != ruamel_task.get('name'):
            raise RuntimeError('Error in matching skip comment to a task')
        pyyaml_task['skipped_rules'] = _get_rule_skips_from_yaml(ruamel_task)

    return pyyaml_data


def _get_task_blocks_from_playbook(playbook):
    """Return parts of playbook that contains tasks, and nested tasks.

    :param playbook: playbook yaml from yaml parser.
    :returns: list of task dictionaries.
    """
    PLAYBOOK_TASK_KEYWORDS = [
        'tasks',
        'pre_tasks',
        'post_tasks',
        'handlers',
    ]

    task_blocks = []
    for play, key in product(playbook, PLAYBOOK_TASK_KEYWORDS):
        task_blocks.extend(play.get(key, []))
    return task_blocks


def _get_tasks_from_blocks(task_blocks):
    """Get list of tasks from list made of tasks and nested tasks."""
    NESTED_TASK_KEYS = [
        'block',
        'always',
        'rescue',
    ]

    def get_nested_tasks(task):
        return (
            subtask
            for k in NESTED_TASK_KEYS if k in task
            for subtask in task[k]
        )

    for task in task_blocks:
        for sub_task in get_nested_tasks(task):
            yield sub_task
        yield task


def _get_rule_skips_from_yaml(yaml_input):
    """Travese yaml for comments with rule skips and return list of rules."""
    def traverse_yaml(obj):
        yaml_comment_obj_strs.append(str(obj.ca.items))
        if isinstance(obj, dict):
            for key, val in obj.items():
                if isinstance(val, (dict, list)):
                    traverse_yaml(val)
        elif isinstance(obj, list):
            for e in obj:
                if isinstance(e, (dict, list)):
                    traverse_yaml(e)
        else:
            return

    yaml_comment_obj_strs = []
    traverse_yaml(yaml_input)

    rule_id_list = []
    for comment_obj_str in yaml_comment_obj_strs:
        for line in comment_obj_str.split('\\n'):
            rule_id_list.extend(get_rule_skips_from_line(line))

    return rule_id_list


def get_rule_skips_from_line(line):
    rule_id_list = []
    if '# noqa' in line:
        noqa_text = line.split('# noqa')[1]
        rule_id_list = noqa_text.split()
    return rule_id_list


def normpath(path):
    """
    Normalize a path in order to provide a more consistent output.

    Currently it generates a relative path but in the future we may want to
    make this user configurable.
    """
    return os.path.relpath(path)


def is_playbook(filename):
    """
    Check if the file is a playbook.

    Given a filename, it should return true if it looks like a playbook. The
    function is not supposed to raise exceptions.
    """
    # we assume is a playbook if we loaded a sequence of dictionaries where
    # at least one of these keys is present:
    playbooks_keys = {
        "gather_facts",
        "hosts",
        "import_playbook",
        "post_tasks",
        "pre_tasks",
        "roles"
        "tasks",
    }

    # makes it work with Path objects by converting them to strings
    if not isinstance(filename, six.string_types):
        filename = str(filename)

    try:
        f = parse_yaml_from_file(filename)
    except Exception as e:
        print(
            "Warning: Failed to load %s with %s, assuming is not a playbook."
            % (filename, e))
    else:
        if (
            isinstance(f, AnsibleSequence)
            and playbooks_keys.intersection(next(iter(f), {}).keys())
        ):
            return True
    return False


def get_playbooks_and_roles(options=None):
    """Find roles and playbooks."""
    if options is None:
        options = {}

    # git is preferred as it also considers .gitignore
    files = OrderedDict.fromkeys(sorted(subprocess.check_output(
        ["git", "ls-files", "*.yaml", "*.yml"],
        universal_newlines=True).split()))

    playbooks = []
    role_dirs = []
    role_internals = {
        'defaults',
        'files',
        'handlers',
        'meta',
        'tasks',
        'templates',
        'vars',
    }

    # detect role in repository root:
    if 'tasks/main.yml' in files:
        role_dirs.append('.')

    for p in map(Path, files):

        if any(str(p).startswith(file_path) for file_path in options.exclude_paths):
            continue
        elif (next((i for i in p.parts if i.endswith('playbooks')), None)
                or 'playbook' in p.parts[-1]):
            playbooks.append(normpath(p))
            continue

        # ignore if any folder ends with _vars
        if next((i for i in p.parts if i.endswith('_vars')), None):
            continue
        elif 'roles' in p.parts or '.' in role_dirs:
            if 'tasks' in p.parts and p.parts[-1] == 'main.yaml':
                role_dirs.append(str(p.parents[1]))
            elif role_internals.intersection(p.parts):
                continue
            elif 'tests' in p.parts:
                playbooks.append(normpath(p))
        if 'molecule' in p.parts:
            if p.parts[-1] != 'molecule.yml':
                playbooks.append(normpath(p))
            continue
        # hidden files are clearly not playbooks, likely config files.
        if p.parts[-1].startswith('.'):
            continue

        if is_playbook(p):
            playbooks.append(normpath(p))
            continue

        if options.verbosity:
            print('Unknown file type: %s' % normpath(p))

    if options.verbosity:
        print('Found roles: ' + ' '.join(role_dirs))
        print('Found playbooks: ' + ' '.join(playbooks))

    return role_dirs + playbooks
