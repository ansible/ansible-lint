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
from argparse import Namespace
from collections.abc import ItemsView
from functools import lru_cache
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import yaml
from ansible import constants
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.mod_args import ModuleArgsParser
from ansible.parsing.splitter import split_args
from ansible.parsing.yaml.constructor import AnsibleConstructor, AnsibleMapping
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleSequence
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

from ansiblelint._internal.rules import (
    AnsibleParserErrorRule,
    LoadingFailureRule,
    RuntimeErrorRule,
)
from ansiblelint.config import options
from ansiblelint.constants import FileType
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable, discover_lintables
from ansiblelint.text import removeprefix

# ansible-lint doesn't need/want to know about encrypted secrets, so we pass a
# string as the password to enable such yaml files to be opened and parsed
# successfully.
DEFAULT_VAULT_PASSWORD = 'x'

PLAYBOOK_DIR = os.environ.get('ANSIBLE_PLAYBOOK_DIR', None)


_logger = logging.getLogger(__name__)


def parse_yaml_from_file(filepath: str) -> AnsibleBaseYAMLObject:
    """Extract a decrypted YAML object from file."""
    dl = DataLoader()
    if hasattr(dl, 'set_vault_password'):
        dl.set_vault_password(DEFAULT_VAULT_PASSWORD)
    return dl.load_from_file(filepath)


def path_dwim(basedir: str, given: str) -> str:
    """Convert a given path do-what-I-mean style."""
    dl = DataLoader()
    dl.set_basedir(basedir)
    return str(dl.path_dwim(given))


def ansible_template(
    basedir: str, varname: Any, templatevars: Any, **kwargs: Any
) -> Any:
    """Render a templated string."""
    # `basedir` is the directory containing the lintable file.
    # Therefore, for tasks in a role, `basedir` has the form
    # `roles/some_role/tasks`. On the other hand, the search path
    # is `roles/some_role/{files,templates}`. As a result, the
    # `tasks` part in the basedir should be stripped stripped.
    if os.path.basename(basedir) == 'tasks':
        basedir = os.path.dirname(basedir)

    dl = DataLoader()
    dl.set_basedir(basedir)
    templar = Templar(dl, variables=templatevars)
    return templar.template(varname, **kwargs)


LINE_NUMBER_KEY = '__line__'
FILENAME_KEY = '__file__'

VALID_KEYS = [
    'name',
    'action',
    'when',
    'async',
    'poll',
    'notify',
    'first_available_file',
    'include',
    'include_tasks',
    'import_tasks',
    'import_playbook',
    'tags',
    'register',
    'ignore_errors',
    'delegate_to',
    'local_action',
    'transport',
    'remote_user',
    'sudo',
    'sudo_user',
    'sudo_pass',
    'when',
    'connection',
    'environment',
    'args',
    'any_errors_fatal',
    'changed_when',
    'failed_when',
    'check_mode',
    'delay',
    'retries',
    'until',
    'su',
    'su_user',
    'su_pass',
    'no_log',
    'run_once',
    'become',
    'become_user',
    'become_method',
    FILENAME_KEY,
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


def tokenize(line: str) -> Tuple[str, List[str], Dict[str, str]]:
    """Parse a string task invocation."""
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


def _playbook_items(pb_data: AnsibleBaseYAMLObject) -> ItemsView:  # type: ignore
    if isinstance(pb_data, dict):
        return pb_data.items()
    if not pb_data:
        return []  # type: ignore

    # "if play" prevents failure if the play sequence contains None,
    # which is weird but currently allowed by Ansible
    # https://github.com/ansible-community/ansible-lint/issues/849
    return [item for play in pb_data if play for item in play.items()]  # type: ignore


def _set_collections_basedir(basedir: str) -> None:
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


def find_children(lintable: Lintable) -> List[Lintable]:  # noqa: C901
    """Traverse children of a single file or folder."""
    if not lintable.path.exists():
        return []
    playbook_dir = str(lintable.path.parent)
    _set_collections_basedir(playbook_dir or os.path.abspath('.'))
    add_all_plugin_dirs(playbook_dir or '.')
    if lintable.kind == 'role':
        playbook_ds = AnsibleMapping({'roles': [{'role': str(lintable.path)}]})
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
        raise MatchError(filename=str(lintable.path), rule=LoadingFailureRule())
    for item in _playbook_items(playbook_ds):
        # if lintable.kind not in ["playbook"]:
        #     continue
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


def template(
    basedir: str,
    value: Any,
    variables: Any,
    fail_on_undefined: bool = False,
    **kwargs: str,
) -> Any:
    """Attempt rendering a value with known vars."""
    try:
        value = ansible_template(
            os.path.abspath(basedir),
            value,
            variables,
            **dict(kwargs, fail_on_undefined=fail_on_undefined),
        )
        # Hack to skip the following exception when using to_json filter on a variable.
        # I guess the filter doesn't like empty vars...
    except (AnsibleError, ValueError, RepresenterError):
        # templating failed, so just keep value as is.
        pass
    return value


def play_children(
    basedir: str, item: Tuple[str, Any], parent_type: FileType, playbook_dir: str
) -> List[Lintable]:
    """Flatten the traversed play tasks."""
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
            v = template(
                os.path.abspath(basedir),
                v,
                dict(playbook_dir=PLAYBOOK_DIR or os.path.abspath(basedir)),
                fail_on_undefined=False,
            )
            return delegate_map[k](basedir, k, v, parent_type)
    return []


def _include_children(
    basedir: str, k: str, v: Any, parent_type: FileType
) -> List[Lintable]:
    # handle special case include_tasks: name=filename.yml
    if k == 'include_tasks' and isinstance(v, dict) and 'file' in v:
        v = v['file']

    # handle include: filename.yml tags=blah
    (command, args, kwargs) = tokenize("{0}: {1}".format(k, v))

    result = path_dwim(basedir, args[0])
    if not os.path.exists(result):
        result = path_dwim(os.path.join(os.path.dirname(basedir)), v)
    return [Lintable(result, kind=parent_type)]


def _taskshandlers_children(
    basedir: str, k: str, v: Union[None, Any], parent_type: FileType
) -> List[Lintable]:
    results: List[Lintable] = []
    if v is None:
        raise MatchError(
            message="A malformed block was encountered while loading a block.",
            rule=RuntimeErrorRule(),
        )
    for th in v:

        # ignore empty tasks, `-`
        if not th:
            continue

        with contextlib.suppress(LookupError):
            children = _get_task_handler_children_for_tasks_or_playbooks(
                th,
                basedir,
                k,
                parent_type,
            )
            results.append(children)
            continue

        if (
            'include_role' in th or 'import_role' in th
        ):  # lgtm [py/unreachable-statement]
            th = normalize_task_v2(th)
            _validate_task_handler_action_for_role(th['action'])
            results.extend(
                _roles_children(
                    basedir,
                    k,
                    [th['action'].get("name")],
                    parent_type,
                    main=th['action'].get('tasks_from', 'main'),
                )
            )
            continue

        if 'block' not in th:
            continue

        results.extend(_taskshandlers_children(basedir, k, th['block'], parent_type))
        if 'rescue' in th:
            results.extend(
                _taskshandlers_children(basedir, k, th['rescue'], parent_type)
            )
        if 'always' in th:
            results.extend(
                _taskshandlers_children(basedir, k, th['always'], parent_type)
            )

    return results


def _get_task_handler_children_for_tasks_or_playbooks(
    task_handler: Dict[str, Any],
    basedir: str,
    k: Any,
    parent_type: FileType,
) -> Lintable:
    """Try to get children of taskhandler for include/import tasks/playbooks."""
    child_type = k if parent_type == 'playbook' else parent_type

    task_include_keys = 'include', 'include_tasks', 'import_playbook', 'import_tasks'
    for task_handler_key in task_include_keys:

        with contextlib.suppress(KeyError):

            # ignore empty tasks
            if not task_handler:
                continue

            # import pdb; pdb.set_trace()
            return Lintable(
                path_dwim(basedir, task_handler[task_handler_key]), kind=child_type
            )

    raise LookupError(
        f'The node contains none of: {", ".join(task_include_keys)}',
    )


def _validate_task_handler_action_for_role(th_action: Dict[str, Any]) -> None:
    """Verify that the task handler action is valid for role include."""
    module = th_action['__ansible_module__']

    if 'name' not in th_action:
        raise MatchError(message=f"Failed to find required 'name' key in {module!s}")

    if not isinstance(th_action['name'], str):
        raise MatchError(
            message=f"Value assigned to 'name' key on '{module!s}' is not a string.",
        )


def _roles_children(
    basedir: str, k: str, v: Sequence[Any], parent_type: FileType, main: str = 'main'
) -> List[Lintable]:
    results: List[Lintable] = []
    for role in v:
        if isinstance(role, dict):
            if 'role' in role or 'name' in role:
                if 'tags' not in role or 'skip_ansible_lint' not in role['tags']:
                    results.extend(
                        _look_for_role_files(
                            basedir, role.get('role', role.get('name')), main=main
                        )
                    )
            elif k != 'dependencies':
                raise SystemExit(
                    'role dict {0} does not contain a "role" '
                    'or "name" key'.format(role)
                )
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
        path_dwim(basedir, os.path.join('..', '..', '..', 'roles', role)),
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


def _look_for_role_files(
    basedir: str, role: str, main: Optional[str] = 'main'
) -> List[Lintable]:
    role_path = _rolepath(basedir, role)
    if not role_path:
        return []

    results = []

    for kind in ['tasks', 'meta', 'handlers', 'vars', 'defaults']:
        current_path = os.path.join(role_path, kind)
        for folder, subdirs, files in os.walk(current_path):
            for file in files:
                file_ignorecase = file.lower()
                if file_ignorecase.endswith(('.yml', '.yaml')):
                    thpath = os.path.join(folder, file)
                    results.append(Lintable(thpath))

    return results


def _kv_to_dict(v: str) -> Dict[str, Any]:
    (command, args, kwargs) = tokenize(v)
    return dict(__ansible_module__=command, __ansible_arguments__=args, **kwargs)


def _sanitize_task(task: Dict[str, Any]) -> Dict[str, Any]:
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


def normalize_task_v2(task: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure tasks have a normalized action key and strings are converted to python objects."""
    result = dict()

    sanitized_task = _sanitize_task(task)
    mod_arg_parser = ModuleArgsParser(sanitized_task)
    try:
        action, arguments, result['delegate_to'] = mod_arg_parser.parse(
            skip_action_validation=options.skip_action_validation
        )
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

    if not isinstance(action, str):
        raise RuntimeError("Task actions can only be strings, got %s" % action)
    action_unnormalized = action
    # convert builtin fqn calls to short forms because most rules know only
    # about short calls but in the future we may switch the normalization to do
    # the opposite. Mainly we currently consider normalized the module listing
    # used by `ansible-doc -t module -l 2>/dev/null`
    action = removeprefix(action, "ansible.builtin.")
    result['action'] = dict(
        __ansible_module__=action, __ansible_module_original__=action_unnormalized
    )

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


def normalize_task(task: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """Unify task-like object structures."""
    ansible_action_type = task.get('__ansible_action_type__', 'task')
    if '__ansible_action_type__' in task:
        del task['__ansible_action_type__']
    task = normalize_task_v2(task)
    task[FILENAME_KEY] = filename
    task['__ansible_action_type__'] = ansible_action_type
    return task


def task_to_str(task: Dict[str, Any]) -> str:
    """Make a string identifier for the given task."""
    name = task.get("name")
    if name:
        return str(name)
    action = task.get("action")
    if isinstance(action, str) or not isinstance(action, dict):
        return str(action)
    args = " ".join(
        [
            "{0}={1}".format(k, v)
            for (k, v) in action.items()
            if k
            not in [
                "__ansible_module__",
                "__ansible_module_original__",
                "__ansible_arguments__",
                "__line__",
                "__file__",
            ]
        ]
    )
    for item in action.get("__ansible_arguments__", []):
        args += f" {item}"
    return u"{0} {1}".format(action["__ansible_module__"], args)


def extract_from_list(
    blocks: AnsibleBaseYAMLObject, candidates: List[str]
) -> List[Any]:
    """Get action tasks from block structures."""
    results = list()
    for block in blocks:
        for candidate in candidates:
            if isinstance(block, dict) and candidate in block:
                if isinstance(block[candidate], list):
                    results.extend(add_action_type(block[candidate], candidate))
                elif block[candidate] is not None:
                    raise RuntimeError(
                        "Key '%s' defined, but bad value: '%s'"
                        % (candidate, str(block[candidate]))
                    )
    return results


def add_action_type(actions: AnsibleBaseYAMLObject, action_type: str) -> List[Any]:
    """Add action markers to task objects."""
    results = list()
    for action in actions:
        # ignore empty task
        if not action:
            continue
        action['__ansible_action_type__'] = BLOCK_NAME_TO_ACTION_TYPE_MAP[action_type]
        results.append(action)
    return results


def get_action_tasks(yaml: AnsibleBaseYAMLObject, file: Lintable) -> List[Any]:
    """Get a flattened list of action tasks from the file."""
    tasks = list()
    if file.kind in ['tasks', 'handlers']:
        tasks = add_action_type(yaml, file.kind)
    else:
        tasks.extend(
            extract_from_list(yaml, ['tasks', 'handlers', 'pre_tasks', 'post_tasks'])
        )

    # Add sub-elements of block/rescue/always to tasks list
    tasks.extend(extract_from_list(tasks, ['block', 'rescue', 'always']))
    # Remove block/rescue/always elements from tasks list
    block_rescue_always = ('block', 'rescue', 'always')
    tasks[:] = [
        task for task in tasks if all(k not in task for k in block_rescue_always)
    ]

    return [
        task
        for task in tasks
        if set(
            ['include', 'include_tasks', 'import_playbook', 'import_tasks']
        ).isdisjoint(task.keys())
    ]


def get_normalized_tasks(
    yaml: "AnsibleBaseYAMLObject", file: Lintable
) -> List[Dict[str, Any]]:
    """Extract normalized tasks from a file."""
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
def parse_yaml_linenumbers(lintable: Lintable) -> AnsibleBaseYAMLObject:
    """Parse yaml as ansible.utils.parse_yaml but with linenumbers.

    The line numbers are stored in each node's LINE_NUMBER_KEY key.
    """

    def compose_node(parent: yaml.nodes.Node, index: int) -> yaml.nodes.Node:
        # the line number where the previous token has ended (plus empty lines)
        line = loader.line
        node = Composer.compose_node(loader, parent, index)
        if not isinstance(node, yaml.nodes.Node):
            raise RuntimeError("Unexpected yaml data.")
        setattr(node, '__line__', line + 1)
        return node

    def construct_mapping(
        node: AnsibleBaseYAMLObject, deep: bool = False
    ) -> AnsibleMapping:
        mapping = AnsibleConstructor.construct_mapping(loader, node, deep=deep)
        if hasattr(node, '__line__'):
            mapping[LINE_NUMBER_KEY] = node.__line__
        else:
            mapping[LINE_NUMBER_KEY] = mapping._line_number
        mapping[FILENAME_KEY] = lintable.path
        return mapping

    try:
        kwargs = {}
        if 'vault_password' in inspect.getfullargspec(AnsibleLoader.__init__).args:
            kwargs['vault_password'] = DEFAULT_VAULT_PASSWORD
        loader = AnsibleLoader(lintable.content, **kwargs)
        loader.compose_node = compose_node
        loader.construct_mapping = construct_mapping
        data = loader.get_single_data()
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
        logging.exception(e)
        raise SystemExit("Failed to parse YAML in %s: %s" % (lintable.path, str(e)))
    return data


def get_first_cmd_arg(task: Dict[str, Any]) -> Any:
    """Extract the first arg from a cmd task."""
    try:
        if 'cmd' in task['action']:
            first_cmd_arg = task['action']['cmd'].split()[0]
        else:
            first_cmd_arg = task['action']['__ansible_arguments__'][0]
    except IndexError:
        return None
    return first_cmd_arg


def get_second_cmd_arg(task: Dict[str, Any]) -> Any:
    """Extract the second arg from a cmd task."""
    try:
        if 'cmd' in task['action']:
            second_cmd_arg = task['action']['cmd'].split()[1]
        else:
            second_cmd_arg = task['action']['__ansible_arguments__'][1]
    except IndexError:
        return None
    return second_cmd_arg


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
        "roles",
        "tasks",
    }

    # makes it work with Path objects by converting them to strings
    if not isinstance(filename, str):
        filename = str(filename)

    try:
        f = parse_yaml_from_file(filename)
    except Exception as e:
        _logger.warning(
            "Failed to load %s with %s, assuming is not a playbook.", filename, e
        )
    else:
        if (
            isinstance(f, AnsibleSequence)
            and hasattr(next(iter(f), {}), 'keys')
            and playbooks_keys.intersection(next(iter(f), {}).keys())
        ):
            return True
    return False


# pylint: disable=too-many-statements
def get_lintables(
    options: Namespace = Namespace(), args: Optional[List[str]] = None
) -> List[Lintable]:
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
                    arg,
                )
                lintable = Lintable(arg, kind="playbook")
            lintables.append(lintable)
    else:

        for filename in discover_lintables(options):

            p = Path(filename)
            # skip exclusions
            try:
                for file_path in options.exclude_paths:
                    if str(p.resolve()).startswith(str(file_path)):
                        raise FileNotFoundError(
                            f'File {file_path} matched exclusion entry: {p}'
                        )
            except FileNotFoundError as e:
                _logger.debug('Ignored %s due to: %s', p, e)
                continue

            lintables.append(Lintable(p))

        # stage 2: guess roles from current lintables, as there is no unique
        # file that must be present in any kind of role.
        _extend_with_roles(lintables)

    return lintables


def _extend_with_roles(lintables: List[Lintable]) -> None:
    """Detect roles among lintables and adds them to the list."""
    for lintable in lintables:
        parts = lintable.path.parent.parts
        if 'roles' in parts:
            role = lintable.path
            while role.parent.name != "roles" and role.name:
                role = role.parent
            if role.exists and not role.is_file():
                lintable = Lintable(role, kind="role")
                if lintable not in lintables:
                    _logger.debug("Added role: %s", lintable)
                    lintables.append(lintable)


def convert_to_boolean(value: Any) -> bool:
    """Use Ansible to convert something to a boolean."""
    return bool(boolean(value))


def nested_items(
    data: Union[Dict[Any, Any], List[Any]], parent: str = ""
) -> Generator[Tuple[Any, Any, str], None, None]:
    """Iterate a nested data structure."""
    if isinstance(data, dict):
        for k, v in data.items():
            yield k, v, parent
            for k, v, p in nested_items(v, k):
                yield k, v, p
    if isinstance(data, list):
        for item in data:
            yield "list-item", item, parent
            for k, v, p in nested_items(item):
                yield k, v, p
