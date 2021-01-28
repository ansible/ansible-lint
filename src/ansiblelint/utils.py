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
"""Generic utility helpers."""

import contextlib
import inspect
import logging
import os
import subprocess
from argparse import Namespace
from collections import OrderedDict
from collections.abc import ItemsView
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml
from ansible import constants
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.mod_args import ModuleArgsParser
from ansible.parsing.splitter import split_args
from ansible.parsing.yaml.constructor import AnsibleConstructor
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.objects import AnsibleSequence
from ansible.plugins.loader import add_all_plugin_dirs
from ansible.template import Templar

try:
    from ansible.module_utils.parsing.convert_bool import boolean
except ImportError:
    try:
        from ansible.utils.boolean import boolean
    except ImportError:
        try:
            from ansible.utils import boolean
        except ImportError:
            boolean = constants.mk_boolean

from yaml.composer import Composer
from yaml.representer import RepresenterError

from ansiblelint._internal.rules import AnsibleParserErrorRule, LoadingFailureRule, RuntimeErrorRule
from ansiblelint.constants import FileType
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable

# ansible-lint doesn't need/want to know about encrypted secrets, so we pass a
# string as the password to enable such yaml files to be opened and parsed
# successfully.
DEFAULT_VAULT_PASSWORD = 'x'

PLAYBOOK_DIR = os.environ.get('ANSIBLE_PLAYBOOK_DIR', None)


_logger = logging.getLogger(__name__)


def parse_yaml_from_file(filepath: str) -> dict:
    dl = DataLoader()
    if hasattr(dl, 'set_vault_password'):
        dl.set_vault_password(DEFAULT_VAULT_PASSWORD)
    return dl.load_from_file(filepath)


def path_dwim(basedir: str, given: str) -> str:
    dl = DataLoader()
    dl.set_basedir(basedir)
    return dl.path_dwim(given)


def ansible_template(basedir: str, varname: Any, templatevars, **kwargs) -> Any:
    dl = DataLoader()
    dl.set_basedir(basedir)
    templar = Templar(dl, variables=templatevars)
    return templar.template(varname, **kwargs)


LINE_NUMBER_KEY = '__line__'
FILENAME_KEY = '__file__'

VALID_KEYS = [
    'name', 'action', 'when', 'async', 'poll', 'notify',
    'first_available_file', 'include', 'include_tasks', 'import_tasks', 'import_playbook',
    'tags', 'register', 'ignore_errors', 'delegate_to',
    'local_action', 'transport', 'remote_user', 'sudo',
    'sudo_user', 'sudo_pass', 'when', 'connection', 'environment', 'args',
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


def tokenize(line: str) -> Tuple[str, List[str], Dict]:
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


def _playbook_items(pb_data: dict) -> ItemsView:
    if isinstance(pb_data, dict):
        return pb_data.items()
    if not pb_data:
        return []
    # "if play" prevents failure if the play sequence containes None,
    # which is weird but currently allowed by Ansible
    # https://github.com/ansible-community/ansible-lint/issues/849
    return [item for play in pb_data if play for item in play.items()]


def _set_collections_basedir(basedir: str):
    # Sets the playbook directory as playbook_paths for the collection loader
    try:
        # Ansible 2.10+
        # noqa: # pylint:disable=cyclic-import,import-outside-toplevel
        from ansible.utils.collection_loader import AnsibleCollectionConfig

        AnsibleCollectionConfig.playbook_paths = basedir
    except ImportError:
        # Ansible 2.8 or 2.9
        # noqa: # pylint:disable=cyclic-import,import-outside-toplevel
        from ansible.utils.collection_loader import set_collection_playbook_paths

        set_collection_playbook_paths(basedir)


def find_children(lintable: Lintable) -> List[Lintable]:
    if not lintable.path.exists():
        return []
    playbook_dir = str(lintable.path.parent)
    _set_collections_basedir(playbook_dir or os.path.abspath('.'))
    add_all_plugin_dirs(playbook_dir or '.')
    if lintable.kind == 'role':
        playbook_ds = {'roles': [{'role': str(lintable.path)}]}
    elif lintable.kind not in ("playbook", "tasks"):
        return []
    else:
        try:
            playbook_ds = parse_yaml_from_file(str(lintable.path))
        except AnsibleError as e:
            raise SystemExit(str(e))
    results = []
    basedir = os.path.dirname(str(lintable.path))
    # playbook_ds can be an AnsibleUnicode string, which we consider invalid
    if isinstance(playbook_ds, str):
        raise MatchError(
            filename=str(lintable.path),
            rule=LoadingFailureRule)
    items = _playbook_items(playbook_ds)
    for item in items:
        for child in play_children(basedir, item, lintable.kind, playbook_dir):
            # We avoid processing parametrized children
            path_str = str(child.path)
            if "$" in path_str or "{{" in path_str:
                continue

            # Repair incorrect paths obtained when old syntax was used, like:
            # - include: simpletask.yml tags=nginx
            valid_tokens = list()
            for token in split_args(path_str):
                if '=' in token:
                    break
                valid_tokens.append(token)
            path = ' '.join(valid_tokens)
            if path != path_str:
                child.path = Path(path)
                child.name = child.path.name

            results.append(child)
    return results


def template(basedir: str, value: Any, variables, fail_on_undefined=False, **kwargs) -> Any:
    try:
        value = ansible_template(os.path.abspath(basedir), value, variables,
                                 **dict(kwargs, fail_on_undefined=fail_on_undefined))
        # Hack to skip the following exception when using to_json filter on a variable.
        # I guess the filter doesn't like empty vars...
    except (AnsibleError, ValueError, RepresenterError):
        # templating failed, so just keep value as is.
        pass
    return value


def play_children(
        basedir: str,
        item: Tuple[str, Any],
        parent_type, playbook_dir) -> List[Lintable]:
    delegate_map: Dict[str, Callable[[str, Any, Any, FileType], List[Lintable]]] = {
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
    add_all_plugin_dirs(os.path.abspath(basedir))

    if k in delegate_map:
        if v:
            v = template(os.path.abspath(basedir),
                         v,
                         dict(playbook_dir=PLAYBOOK_DIR or os.path.abspath(basedir)),
                         fail_on_undefined=False)
            return delegate_map[k](basedir, k, v, parent_type)
    return []


def _include_children(basedir: str, k, v, parent_type) -> List[Lintable]:
    # handle special case include_tasks: name=filename.yml
    if k == 'include_tasks' and isinstance(v, dict) and 'file' in v:
        v = v['file']

    # handle include: filename.yml tags=blah
    (command, args, kwargs) = tokenize("{0}: {1}".format(k, v))

    result = path_dwim(basedir, args[0])
    if not os.path.exists(result):
        result = path_dwim(os.path.join(os.path.dirname(basedir)), v)
    return [Lintable(result, kind=parent_type)]


def _taskshandlers_children(basedir, k, v, parent_type: FileType) -> List[Lintable]:
    results: List[Lintable] = []
    if v is None:
        raise MatchError(
            message="A malformed block was encountered while loading a block.",
            rule=RuntimeErrorRule())
    for th in v:

        # ignore empty tasks, `-`
        if not th:
            continue

        with contextlib.suppress(LookupError):
            children = _get_task_handler_children_for_tasks_or_playbooks(
                th, basedir, k, parent_type,
            )
            results.append(children)
            continue

        if 'include_role' in th or 'import_role' in th:  # lgtm [py/unreachable-statement]
            th = normalize_task_v2(th)
            _validate_task_handler_action_for_role(th['action'])
            results.extend(_roles_children(basedir, k, [th['action'].get("name")],
                                           parent_type,
                                           main=th['action'].get('tasks_from', 'main')))
            continue

        if 'block' not in th:
            continue

        results.extend(_taskshandlers_children(basedir, k, th['block'], parent_type))
        if 'rescue' in th:
            results.extend(_taskshandlers_children(basedir, k, th['rescue'], parent_type))
        if 'always' in th:
            results.extend(_taskshandlers_children(basedir, k, th['always'], parent_type))

    return results


def _get_task_handler_children_for_tasks_or_playbooks(
        task_handler, basedir: str, k, parent_type: FileType,
) -> Lintable:
    """Try to get children of taskhandler for include/import tasks/playbooks."""
    child_type = k if parent_type == 'playbook' else parent_type

    task_include_keys = 'include', 'include_tasks', 'import_playbook', 'import_tasks'
    for task_handler_key in task_include_keys:

        with contextlib.suppress(KeyError):

            # ignore empty tasks
            if not task_handler:
                continue

            return Lintable(
                path_dwim(basedir, task_handler[task_handler_key]),
                kind=child_type)

    raise LookupError(
        f'The node contains none of: {", ".join(task_include_keys)}',
    )


def _validate_task_handler_action_for_role(th_action: dict) -> None:
    """Verify that the task handler action is valid for role include."""
    module = th_action['__ansible_module__']

    if 'name' not in th_action:
        raise MatchError(
            message=f"Failed to find required 'name' key in {module!s}")

    if not isinstance(th_action['name'], str):
        raise MatchError(
            message=f"Value assigned to 'name' key on '{module!s}' is not a string.",
        )


def _roles_children(basedir: str, k, v, parent_type: FileType, main='main') -> List[Lintable]:
    results: List[Lintable] = []
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


def _rolepath(basedir: str, role: str) -> Optional[str]:
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
        # if checking a role in the current directory
        path_dwim(basedir, os.path.join('..', role)),
    ]

    if constants.DEFAULT_ROLES_PATH:
        search_locations = constants.DEFAULT_ROLES_PATH
        if isinstance(search_locations, str):
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
        add_all_plugin_dirs(role_path)

    return role_path


def _look_for_role_files(basedir: str, role: str, main='main') -> List[Lintable]:
    role_path = _rolepath(basedir, role)
    if not role_path:
        return []

    results = []

    for kind in ['tasks', 'meta', 'handlers']:
        current_path = os.path.join(role_path, kind)
        for folder, subdirs, files in os.walk(current_path):
            for file in files:
                file_ignorecase = file.lower()
                if file_ignorecase.endswith(('.yml', '.yaml')):
                    thpath = os.path.join(folder, file)
                    # TODO(ssbarnea): Find correct way to pass kind: FileType
                    results.append(
                        Lintable(thpath, kind=kind))  # type: ignore

    return results


def rolename(filepath):
    idx = filepath.find('roles/')
    if idx < 0:
        return ''
    role = filepath[idx + 6:]
    role = role[:role.find('/')]
    return role


def _kv_to_dict(v):
    (command, args, kwargs) = tokenize(v)
    return dict(__ansible_module__=command, __ansible_arguments__=args, **kwargs)


def _sanitize_task(task: dict) -> dict:
    """Return a stripped-off task structure compatible with new Ansible.

    This helper takes a copy of the incoming task and drops
    any internally used keys from it.
    """
    result = task.copy()
    # task is an AnsibleMapping which inherits from OrderedDict, so we need
    # to use `del` to remove unwanted keys.
    for k in ['skipped_rules', FILENAME_KEY, LINE_NUMBER_KEY]:
        if k in result:
            del result[k]
    return result


# FIXME: drop noqa once this function is made simpler
# Ref: https://github.com/ansible-community/ansible-lint/issues/744
def normalize_task_v2(task: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
    """Ensure tasks have an action key and strings are converted to python objects."""
    result = dict()

    sanitized_task = _sanitize_task(task)
    mod_arg_parser = ModuleArgsParser(sanitized_task)
    try:
        action, arguments, result['delegate_to'] = mod_arg_parser.parse()
    except AnsibleParserError as e:
        raise MatchError(
            rule=AnsibleParserErrorRule(),
            message=e.message,
            filename=task.get(FILENAME_KEY, "Unknown"),
            linenumber=task.get(LINE_NUMBER_KEY, 0),
            )

    # denormalize shell -> command conversion
    if '_uses_shell' in arguments:
        action = 'shell'
        del arguments['_uses_shell']

    for (k, v) in list(task.items()):
        if k in ('action', 'local_action', 'args', 'delegate_to') or k == action:
            # we don't want to re-assign these values, which were
            # determined by the ModuleArgsParser() above
            continue
        result[k] = v

    result['action'] = dict(__ansible_module__=action)

    if '_raw_params' in arguments:
        result['action']['__ansible_arguments__'] = arguments['_raw_params'].split(' ')
        del arguments['_raw_params']
    else:
        result['action']['__ansible_arguments__'] = list()

    if 'argv' in arguments and not result['action']['__ansible_arguments__']:
        result['action']['__ansible_arguments__'] = arguments['argv']
        del arguments['argv']

    result['action'].update(arguments)
    return result


# FIXME: drop noqa once this function is made simpler
# Ref: https://github.com/ansible-community/ansible-lint/issues/744
def normalize_task_v1(task):  # noqa: C901
    result = dict()
    for (k, v) in task.items():
        if k in VALID_KEYS or k.startswith('with_'):
            if k in ('local_action', 'action'):
                if not isinstance(v, dict):
                    v = _kv_to_dict(v)
                v['__ansible_arguments__'] = v.get('__ansible_arguments__', list())
                result['action'] = v
            else:
                result[k] = v
        else:
            if isinstance(v, str):
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
                    # Tasks that include playbooks (rather than task files)
                    # can get here
                    # https://github.com/ansible-community/ansible-lint/issues/138
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
        del result['action']['module']
    if 'args' in result:
        result['action'].update(result.get('args'))
        del result['args']
    return result


def normalize_task(task: Dict[str, Any], filename: str) -> Dict[str, Any]:
    ansible_action_type = task.get('__ansible_action_type__', 'task')
    if '__ansible_action_type__' in task:
        del task['__ansible_action_type__']
    task = normalize_task_v2(task)
    task[FILENAME_KEY] = filename
    task['__ansible_action_type__'] = ansible_action_type
    return task


def task_to_str(task: Dict[str, Any]) -> str:
    name = task.get("name")
    if name:
        return str(name)
    action = task.get("action")
    if isinstance(action, str) or not isinstance(action, dict):
        return str(action)
    args = " ".join([
        "{0}={1}".format(k, v) for (k, v) in action.items()
        if k not in ["__ansible_module__", "__ansible_arguments__"]])
    for item in action.get("__ansible_arguments__", []):
        args += f" {item}"
    return u"{0} {1}".format(action["__ansible_module__"], args)


def extract_from_list(blocks, candidates: List[str]) -> List[Any]:
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


def add_action_type(actions, action_type: str) -> List[Any]:
    results = list()
    for action in actions:
        # ignore empty task
        if not action:
            continue
        action['__ansible_action_type__'] = BLOCK_NAME_TO_ACTION_TYPE_MAP[action_type]
        results.append(action)
    return results


def get_action_tasks(yaml, file: Lintable) -> List[Any]:
    tasks = list()
    if file.kind in ['tasks', 'handlers']:
        tasks = add_action_type(yaml, file.kind)
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


def get_normalized_tasks(yaml, file: Lintable) -> List[Dict[str, Any]]:
    tasks = get_action_tasks(yaml, file)
    res = []
    for task in tasks:
        # An empty `tags` block causes `None` to be returned if
        # the `or []` is not present - `task.get('tags', [])`
        # does not suffice.
        if 'skip_ansible_lint' in (task.get('tags') or []):
            # No need to normalize_task is we are skipping it.
            continue
        res.append(normalize_task(task, str(file.path)))

    return res


@lru_cache(maxsize=128)
def parse_yaml_linenumbers(data, filename):
    """Parse yaml as ansible.utils.parse_yaml but with linenumbers.

    The line numbers are stored in each node's LINE_NUMBER_KEY key.
    """
    def compose_node(parent, index):
        # the line number where the previous token has ended (plus empty lines)
        line = loader.line
        node = Composer.compose_node(loader, parent, index)
        node.__line__ = line + 1
        return node

    def construct_mapping(node, deep=False):
        mapping = AnsibleConstructor.construct_mapping(loader, node, deep=deep)
        if hasattr(node, '__line__'):
            mapping[LINE_NUMBER_KEY] = node.__line__
        else:
            mapping[LINE_NUMBER_KEY] = mapping._line_number
        mapping[FILENAME_KEY] = filename
        return mapping

    try:
        kwargs = {}
        if 'vault_password' in inspect.getfullargspec(AnsibleLoader.__init__).args:
            kwargs['vault_password'] = DEFAULT_VAULT_PASSWORD
        loader = AnsibleLoader(data, **kwargs)
        loader.compose_node = compose_node
        loader.construct_mapping = construct_mapping
        data = loader.get_single_data()
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
        raise SystemExit("Failed to parse YAML in %s: %s" % (filename, str(e)))
    return data


def get_first_cmd_arg(task: Dict[str, Any]) -> Any:
    try:
        if 'cmd' in task['action']:
            first_cmd_arg = task['action']['cmd'].split()[0]
        else:
            first_cmd_arg = task['action']['__ansible_arguments__'][0]
    except IndexError:
        return None
    return first_cmd_arg


def is_playbook(filename: str) -> bool:
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
    if not isinstance(filename, str):
        filename = str(filename)

    try:
        f = parse_yaml_from_file(filename)
    except Exception as e:
        _logger.warning(
            "Failed to load %s with %s, assuming is not a playbook.",
            filename, e)
    else:
        if (
            isinstance(f, AnsibleSequence) and
            hasattr(next(iter(f), {}), 'keys') and
            playbooks_keys.intersection(next(iter(f), {}).keys())
        ):
            return True
    return False


def get_yaml_files(options: Namespace) -> dict:
    """Find all yaml files."""
    # git is preferred as it also considers .gitignore
    git_command = ['git', 'ls-files', '*.yaml', '*.yml']
    _logger.info("Discovering files to lint: %s", ' '.join(git_command))

    out = None

    try:
        out = subprocess.check_output(
            git_command,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        ).splitlines()
    except subprocess.CalledProcessError as exc:
        _logger.warning(
            "Failed to discover yaml files to lint using git: %s",
            exc.output.rstrip('\n')
        )
    except FileNotFoundError as exc:
        if options.verbosity:
            _logger.warning(
                "Failed to locate command: %s", exc
            )

    if out is None:
        out = [
            os.path.join(root, name)
            for root, dirs, files in os.walk('.')
            for name in files
            if name.endswith('.yaml') or name.endswith('.yml')
        ]

    return OrderedDict.fromkeys(sorted(out))


# pylint: disable=too-many-statements
def get_lintables(
        options: Namespace = Namespace(),
        args: Optional[List[str]] = None) -> List[Lintable]:
    """Detect files and directories that are lintable."""
    lintables: List[Lintable] = []

    # passing args bypass auto-detection mode
    if args:
        for arg in args:
            lintable = Lintable(arg)
            if lintable.kind in ("yaml", None):
                _logger.warning(
                    "Overriding detected file kind '%s' with 'playbook' "
                    "for given positional argument: %s",
                    lintable.kind,
                    arg)
                lintable = Lintable(arg, kind="playbook")
            lintables.append(lintable)
    else:

        for filename in get_yaml_files(options):

            p = Path(filename)
            # skip exclusions
            try:
                for file_path in options.exclude_paths:
                    if str(p.resolve()).startswith(str(file_path)):
                        raise FileNotFoundError(
                            f'File {file_path} matched exclusion entry: {p}')
            except FileNotFoundError as e:
                _logger.debug('Ignored %s due to: %s', p, e)
                continue

            lintables.append(Lintable(p))

        # stage 2: guess roles from current lintables, as there is no unique
        # file that must be present in any kind of role.

        for lintable in lintables:
            parts = lintable.path.parent.parts
            if 'roles' in parts:
                role = lintable.path
                while role.parent.name != "roles" and role.name:
                    role = role.parent
                if role.exists:
                    lintable = Lintable(role, kind="role")
                    if lintable not in lintables:
                        _logger.debug("Added role: %s", lintable)
                        lintables.append(lintable)

    return lintables


def convert_to_boolean(value: Any) -> bool:
    """Use Ansible to convert something to a boolean."""
    return bool(boolean(value))
