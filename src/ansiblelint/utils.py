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
# spell-checker:ignore dwim
# pylint: disable=too-many-lines
"""Generic utility helpers."""
from __future__ import annotations

import ast
import contextlib
import inspect
import logging
import os
import re
from collections.abc import ItemsView, Iterator, Mapping, Sequence
from dataclasses import _MISSING_TYPE, dataclass, field
from functools import cache, lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import ruamel.yaml.parser
import yaml
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.mod_args import ModuleArgsParser
from ansible.parsing.plugin_docs import read_docstring
from ansible.parsing.yaml.constructor import AnsibleConstructor, AnsibleMapping
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleSequence
from ansible.plugins.loader import (
    PluginLoadContext,
    action_loader,
    add_all_plugin_dirs,
    module_loader,
)
from ansible.template import Templar
from ansible.utils.collection_loader import AnsibleCollectionConfig
from yaml.composer import Composer
from yaml.representer import RepresenterError

from ansiblelint._internal.rules import (
    AnsibleParserErrorRule,
    RuntimeErrorRule,
)
from ansiblelint.app import App, get_app
from ansiblelint.config import Options, options
from ansiblelint.constants import (
    ANNOTATION_KEYS,
    FILENAME_KEY,
    INCLUSION_ACTION_NAMES,
    LINE_NUMBER_KEY,
    NESTED_TASK_KEYS,
    PLAYBOOK_TASK_KEYWORDS,
    ROLE_IMPORT_ACTION_NAMES,
    SKIPPED_RULES_KEY,
    FileType,
)
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable, discover_lintables
from ansiblelint.skip_utils import is_nested_task
from ansiblelint.text import has_jinja, removeprefix

if TYPE_CHECKING:
    from ansiblelint.rules import RulesCollection
# ansible-lint doesn't need/want to know about encrypted secrets, so we pass a
# string as the password to enable such yaml files to be opened and parsed
# successfully.
DEFAULT_VAULT_PASSWORD = "x"  # noqa: S105
COLLECTION_PLAY_RE = re.compile(r"^[\w\d_]+\.[\w\d_]+\.[\w\d_]+$")

PLAYBOOK_DIR = os.environ.get("ANSIBLE_PLAYBOOK_DIR", None)


_logger = logging.getLogger(__name__)


def parse_yaml_from_file(filepath: str) -> AnsibleBaseYAMLObject:
    """Extract a decrypted YAML object from file."""
    dataloader = DataLoader()
    if hasattr(dataloader, "set_vault_password"):
        dataloader.set_vault_password(DEFAULT_VAULT_PASSWORD)
    return dataloader.load_from_file(filepath)


def path_dwim(basedir: str, given: str) -> str:
    """Convert a given path do-what-I-mean style."""
    dataloader = DataLoader()
    dataloader.set_basedir(basedir)
    return str(dataloader.path_dwim(given))


def ansible_templar(basedir: Path, templatevars: Any) -> Templar:
    """Create an Ansible Templar using templatevars."""
    # `basedir` is the directory containing the lintable file.
    # Therefore, for tasks in a role, `basedir` has the form
    # `roles/some_role/tasks`. On the other hand, the search path
    # is `roles/some_role/{files,templates}`. As a result, the
    # `tasks` part in the basedir should be stripped stripped.
    if basedir.name == "tasks":
        basedir = basedir.parent

    dataloader = DataLoader()
    dataloader.set_basedir(basedir)
    templar = Templar(dataloader, variables=templatevars)
    return templar


def mock_filter(left: Any, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
    """Mock a filter that can take any combination of args and kwargs.

    This will return x when x | filter(y,z) is called
    e.g. {{ foo | ansible.utils.ipaddr('address') }}

    :param left: The left hand side of the filter
    :param args: The args passed to the filter
    :param kwargs: The kwargs passed to the filter
    :return: The left hand side of the filter
    """
    # pylint: disable=unused-argument
    return left


def ansible_template(
    basedir: Path,
    varname: Any,
    templatevars: Any,
    **kwargs: Any,
) -> Any:
    """Render a templated string by mocking missing filters.

    In the case of a missing lookup, ansible core does an early exit
    when disable_lookup=True but this happens after the jinja2 syntax already passed
    return the original string as if it had been templated.

    In the case of a missing filter, extract the missing filter plugin name
    from the ansible error, 'Could not load "filter"'. Then mock the filter
    and template the string again. The range allows for up to 10 unknown filters
    in succession

    :param basedir: The directory containing the lintable file
    :param varname: The string to be templated
    :param templatevars: The variables to be used in the template
    :param kwargs: Additional arguments to be passed to the templating engine
    :return: The templated string or None
    :raises: AnsibleError if the filter plugin cannot be extracted or the
             string could not be templated in 10 attempts
    """
    # pylint: disable=too-many-locals
    filter_error = "template error while templating string:"
    lookup_error = "was found, however lookups were disabled from templating"
    re_filter_fqcn = re.compile(r"\w+\.\w+\.\w+")
    re_filter_in_err = re.compile(r"Could not load \"(\w+)\"")
    re_valid_filter = re.compile(r"^\w+(\.\w+\.\w+)?$")
    templar = ansible_templar(basedir=basedir, templatevars=templatevars)

    kwargs["disable_lookups"] = True
    for _i in range(10):
        try:
            templated = templar.template(varname, **kwargs)
        except AnsibleError as exc:
            if lookup_error in exc.message:
                return varname
            if exc.message.startswith(filter_error):
                while True:
                    match = re_filter_in_err.search(exc.message)
                    if match:
                        missing_filter = match.group(1)
                        break
                    match = re_filter_fqcn.search(exc.message)
                    if match:
                        missing_filter = match.group(0)
                        break
                    missing_filter = exc.message.split("'")[1]
                    break

                if not re_valid_filter.match(missing_filter):
                    err = f"Could not parse missing filter name from error message: {exc.message}"
                    _logger.warning(err)
                    raise

                templar.environment.filters._delegatee[missing_filter] = mock_filter  # fmt: skip # noqa: SLF001
                # Record the mocked filter so we can warn the user
                if missing_filter not in options.mock_filters:
                    _logger.debug("Mocking missing filter %s", missing_filter)
                    options.mock_filters.append(missing_filter)
                continue
            raise
        return templated
    return None


BLOCK_NAME_TO_ACTION_TYPE_MAP = {
    "tasks": "task",
    "handlers": "handler",
    "pre_tasks": "task",
    "post_tasks": "task",
    "block": "meta",
    "rescue": "meta",
    "always": "meta",
}


def tokenize(line: str) -> tuple[str, list[str], dict[str, str]]:
    """Parse a string task invocation."""
    tokens = line.lstrip().split(" ")
    if tokens[0] == "-":
        tokens = tokens[1:]
    if tokens[0] == "action:" or tokens[0] == "local_action:":
        tokens = tokens[1:]
    command = tokens[0].replace(":", "")

    args = []
    kwargs = {}
    non_kv_found = False
    for arg in tokens[1:]:
        if "=" in arg and not non_kv_found:
            key_value = arg.split("=", 1)
            kwargs[key_value[0]] = key_value[1]
        else:
            non_kv_found = True
            args.append(arg)
    return (command, args, kwargs)


def playbook_items(pb_data: AnsibleBaseYAMLObject) -> ItemsView:  # type: ignore[type-arg]
    """Return a list of items from within the playbook."""
    if isinstance(pb_data, dict):
        return pb_data.items()
    if not pb_data:
        return []  # type: ignore[return-value]

    # "if play" prevents failure if the play sequence contains None,
    # which is weird but currently allowed by Ansible
    # https://github.com/ansible/ansible-lint/issues/849
    return [item for play in pb_data if play for item in play.items()]  # type: ignore[return-value]


def set_collections_basedir(basedir: Path) -> None:
    """Set the playbook directory as playbook_paths for the collection loader."""
    # Ansible expects only absolute paths inside `playbook_paths` and will
    # produce weird errors if we use a relative one.
    AnsibleCollectionConfig.playbook_paths = str(basedir.resolve())


def template(
    basedir: Path,
    value: Any,
    variables: Any,
    *,
    fail_on_error: bool = False,
    fail_on_undefined: bool = False,
    **kwargs: str,
) -> Any:
    """Attempt rendering a value with known vars."""
    try:
        value = ansible_template(
            basedir.resolve(),
            value,
            variables,
            **dict(kwargs, fail_on_undefined=fail_on_undefined),
        )
        # Hack to skip the following exception when using to_json filter on a variable. # noqa: FIX004
        # I guess the filter doesn't like empty vars...
    except (AnsibleError, ValueError, RepresenterError):
        # templating failed, so just keep value as is.
        if fail_on_error:
            raise
    return value


@dataclass
class HandleChildren:
    """Parse task, roles and children."""

    rules: RulesCollection = field(init=True, repr=False)
    app: App

    def include_children(
        self,
        basedir: str,
        k: str,
        v: Any,
        parent_type: FileType,
    ) -> list[Lintable]:
        """Include children."""
        # handle special case include_tasks: name=filename.yml
        if k in INCLUSION_ACTION_NAMES and isinstance(v, dict) and "file" in v:
            v = v["file"]

        # we cannot really parse any jinja2 in includes, so we ignore them
        if not v or "{{" in v:
            return []

        if k in ("import_playbook", "ansible.builtin.import_playbook"):
            included = Path(basedir) / v
            if self.app.runtime.has_playbook(v, basedir=Path(basedir)):
                if included.exists():
                    return [Lintable(included, kind=parent_type)]
                return []
            msg = f"Failed to find {v} playbook."
            logging.error(msg)
            return []

        # handle include: filename.yml tags=blah
        # pylint: disable=unused-variable
        (command, args, kwargs) = tokenize(f"{k}: {v}")

        result = path_dwim(basedir, args[0])
        while basedir not in ["", "/"]:
            if os.path.exists(result):
                break
            basedir = os.path.dirname(basedir)
            result = path_dwim(basedir, args[0])

        return [Lintable(result, kind=parent_type)]

    def taskshandlers_children(
        self,
        basedir: str,
        k: str,
        v: None | Any,
        parent_type: FileType,
    ) -> list[Lintable]:
        """TasksHandlers Children."""
        results: list[Lintable] = []
        if v is None or isinstance(v, int | str):
            raise MatchError(
                message="A malformed block was encountered while loading a block.",
                rule=RuntimeErrorRule(),
            )
        for task_handler in v:
            # ignore empty tasks, `-`
            if not task_handler:
                continue

            with contextlib.suppress(LookupError):
                children = _get_task_handler_children_for_tasks_or_playbooks(
                    task_handler,
                    basedir,
                    k,
                    parent_type,
                )
                results.append(children)
                continue

            if any(x in task_handler for x in ROLE_IMPORT_ACTION_NAMES):
                task_handler = normalize_task_v2(task_handler)
                self._validate_task_handler_action_for_role(task_handler["action"])
                name = task_handler["action"].get("name")
                if has_jinja(name):
                    # we cannot deal with dynamic imports
                    continue
                results.extend(
                    self.roles_children(basedir, k, [name], parent_type),
                )
                continue

            if "block" not in task_handler:
                continue

            results.extend(
                self.taskshandlers_children(
                    basedir,
                    k,
                    task_handler["block"],
                    parent_type,
                ),
            )
            if "rescue" in task_handler:
                results.extend(
                    self.taskshandlers_children(
                        basedir,
                        k,
                        task_handler["rescue"],
                        parent_type,
                    ),
                )
            if "always" in task_handler:
                results.extend(
                    self.taskshandlers_children(
                        basedir,
                        k,
                        task_handler["always"],
                        parent_type,
                    ),
                )

        return results

    def _validate_task_handler_action_for_role(self, th_action: dict[str, Any]) -> None:
        """Verify that the task handler action is valid for role include."""
        module = th_action["__ansible_module__"]

        if "name" not in th_action:
            raise MatchError(
                message=f"Failed to find required 'name' key in {module!s}",
                rule=self.rules.rules[0],
                filename=(
                    self.rules.options.lintables[0]
                    if self.rules.options.lintables
                    else "."
                ),
            )

        if not isinstance(th_action["name"], str):
            raise MatchError(
                message=f"Value assigned to 'name' key on '{module!s}' is not a string.",
                rule=self.rules.rules[1],
            )

    def roles_children(
        self,
        basedir: str,
        k: str,
        v: Sequence[Any],
        parent_type: FileType,
    ) -> list[Lintable]:
        """Roles children."""
        # pylint: disable=unused-argument # parent_type)
        results: list[Lintable] = []
        if not v:
            # typing does not prevent junk from being passed in
            return results
        for role in v:
            if isinstance(role, dict):
                if "role" in role or "name" in role:
                    if "tags" not in role or "skip_ansible_lint" not in role["tags"]:
                        results.extend(
                            _look_for_role_files(
                                basedir,
                                role.get("role", role.get("name")),
                            ),
                        )
                elif k != "dependencies":
                    msg = f'role dict {role} does not contain a "role" or "name" key'
                    raise SystemExit(msg)
            else:
                results.extend(_look_for_role_files(basedir, role))
        return results


def _get_task_handler_children_for_tasks_or_playbooks(
    task_handler: dict[str, Any],
    basedir: str,
    k: Any,
    parent_type: FileType,
) -> Lintable:
    """Try to get children of taskhandler for include/import tasks/playbooks."""
    child_type = k if parent_type == "playbook" else parent_type

    # Include the FQCN task names as this happens before normalize
    for task_handler_key in INCLUSION_ACTION_NAMES:
        with contextlib.suppress(KeyError):
            # ignore empty tasks
            if not task_handler or isinstance(task_handler, str):  # pragma: no branch
                continue

            file_name = task_handler[task_handler_key]
            if isinstance(file_name, Mapping) and file_name.get("file", None):
                file_name = file_name["file"]

            f = path_dwim(basedir, file_name)
            while basedir not in ["", "/"]:
                if os.path.exists(f):
                    break
                basedir = os.path.dirname(basedir)
                f = path_dwim(basedir, file_name)
            return Lintable(f, kind=child_type)
    msg = f'The node contains none of: {", ".join(sorted(INCLUSION_ACTION_NAMES))}'
    raise LookupError(msg)


def _rolepath(basedir: str, role: str) -> str | None:
    role_path = None

    possible_paths = [
        # if included from a playbook
        path_dwim(basedir, os.path.join("roles", role)),
        path_dwim(basedir, role),
        # if included from roles/[role]/meta/main.yml
        path_dwim(basedir, os.path.join("..", "..", "..", "roles", role)),
        path_dwim(basedir, os.path.join("..", "..", role)),
        # if checking a role in the current directory
        path_dwim(basedir, os.path.join("..", role)),
    ]

    for loc in get_app(cached=True).runtime.config.default_roles_path:
        loc = os.path.expanduser(loc)
        possible_paths.append(path_dwim(loc, role))

    possible_paths.append(path_dwim(basedir, ""))

    for path_option in possible_paths:  # pragma: no branch
        if os.path.isdir(path_option):
            role_path = path_option
            break

    if role_path:  # pragma: no branch
        add_all_plugin_dirs(role_path)

    return role_path


def _look_for_role_files(basedir: str, role: str) -> list[Lintable]:
    role_path = _rolepath(basedir, role)
    if not role_path:  # pragma: no branch
        return []

    results = []

    for kind in ["tasks", "meta", "handlers", "vars", "defaults"]:
        current_path = os.path.join(role_path, kind)
        for folder, _, files in os.walk(current_path):
            for file in files:
                file_ignorecase = file.lower()
                if file_ignorecase.endswith((".yml", ".yaml")):
                    results.append(Lintable(os.path.join(folder, file)))

    return results


def _sanitize_task(task: dict[str, Any]) -> dict[str, Any]:
    """Return a stripped-off task structure compatible with new Ansible.

    This helper takes a copy of the incoming task and drops
    any internally used keys from it.
    """
    result = task.copy()
    # task is an AnsibleMapping which inherits from OrderedDict, so we need
    # to use `del` to remove unwanted keys.
    for k in [SKIPPED_RULES_KEY, FILENAME_KEY, LINE_NUMBER_KEY]:
        if k in result:
            del result[k]
    return result


def _extract_ansible_parsed_keys_from_task(
    result: dict[str, Any],
    task: dict[str, Any],
    keys: tuple[str, ...],
) -> dict[str, Any]:
    """Return a dict with existing key in task."""
    for k, v in list(task.items()):
        if k in keys:
            # we don't want to re-assign these values, which were
            # determined by the ModuleArgsParser() above
            continue
        result[k] = v
    return result


def normalize_task_v2(task: dict[str, Any]) -> dict[str, Any]:
    """Ensure tasks have a normalized action key and strings are converted to python objects."""
    result: dict[str, Any] = {}
    ansible_parsed_keys = ("action", "local_action", "args", "delegate_to")

    if is_nested_task(task):
        _extract_ansible_parsed_keys_from_task(result, task, ansible_parsed_keys)
        # Add dummy action for block/always/rescue statements
        result["action"] = {
            "__ansible_module__": "block/always/rescue",
            "__ansible_module_original__": "block/always/rescue",
        }

        return result

    sanitized_task = _sanitize_task(task)
    mod_arg_parser = ModuleArgsParser(sanitized_task)

    try:
        action, arguments, result["delegate_to"] = mod_arg_parser.parse(
            skip_action_validation=options.skip_action_validation,
        )
    except AnsibleParserError as exc:
        raise MatchError(
            rule=AnsibleParserErrorRule(),
            message=exc.message,
            filename=task.get(FILENAME_KEY, "Unknown"),
            lineno=task.get(LINE_NUMBER_KEY, 0),
        ) from exc

    # denormalize shell -> command conversion
    if "_uses_shell" in arguments:
        action = "shell"
        del arguments["_uses_shell"]

    _extract_ansible_parsed_keys_from_task(
        result,
        task,
        (*ansible_parsed_keys, action),
    )

    if not isinstance(action, str):
        msg = f"Task actions can only be strings, got {action}"
        raise TypeError(msg)
    action_unnormalized = action
    # convert builtin fqn calls to short forms because most rules know only
    # about short calls but in the future we may switch the normalization to do
    # the opposite. Mainly we currently consider normalized the module listing
    # used by `ansible-doc -t module -l 2>/dev/null`
    action = removeprefix(action, "ansible.builtin.")
    result["action"] = {
        "__ansible_module__": action,
        "__ansible_module_original__": action_unnormalized,
    }

    result["action"].update(arguments)
    return result


def normalize_task(task: dict[str, Any], filename: str) -> dict[str, Any]:
    """Unify task-like object structures."""
    ansible_action_type = task.get("__ansible_action_type__", "task")
    if "__ansible_action_type__" in task:
        del task["__ansible_action_type__"]
    task = normalize_task_v2(task)
    task[FILENAME_KEY] = filename
    task["__ansible_action_type__"] = ansible_action_type
    return task


def task_to_str(task: dict[str, Any]) -> str:
    """Make a string identifier for the given task."""
    name = task.get("name")
    if name:
        return str(name)
    action = task.get("action")
    if isinstance(action, str) or not isinstance(action, dict):
        return str(action)
    args = [
        f"{k}={v}"
        for (k, v) in action.items()
        if k
        not in [
            "__ansible_module__",
            "__ansible_module_original__",
            "_raw_params",
            LINE_NUMBER_KEY,
            FILENAME_KEY,
        ]
    ]

    _raw_params = action.get("_raw_params", [])
    if isinstance(_raw_params, list):
        for item in _raw_params:
            args.extend(str(item))
    else:
        args.append(_raw_params)

    return f"{action['__ansible_module__']} {' '.join(args)}"


def extract_from_list(
    blocks: AnsibleBaseYAMLObject,
    candidates: list[str],
    *,
    recursive: bool = False,
) -> list[Any]:
    """Get action tasks from block structures."""
    results = []
    for block in blocks:
        for candidate in candidates:
            if isinstance(block, dict) and candidate in block:
                if isinstance(block[candidate], list):
                    subresults = add_action_type(block[candidate], candidate)
                    if recursive:
                        subresults.extend(
                            extract_from_list(
                                subresults,
                                candidates,
                                recursive=recursive,
                            ),
                        )
                    results.extend(subresults)
                elif block[candidate] is not None:
                    msg = f"Key '{candidate}' defined, but bad value: '{block[candidate]!s}'"
                    raise RuntimeError(msg)
    return results


@dataclass
class Task(dict[str, Any]):
    """Class that represents a task from linter point of view.

    raw_task:
        When looping through the tasks in the file, each "raw_task" is minimally
        processed to include these special keys: __line__, __file__, skipped_rules.
    normalized_task:
        When each raw_task is "normalized", action shorthand (strings) get parsed
        by ansible into python objects and the action key gets normalized. If the task
        should be skipped (skipped is True) or normalizing it fails (error is not None)
        then this is just the raw_task instead of a normalized copy.
    skip_tags:
        List of tags found to be skipped, from tags block or noqa comments
    error:
        This is normally None. It will be a MatchError when the raw_task cannot be
        normalized due to an AnsibleParserError.
    position: Any
    """

    raw_task: dict[str, Any]
    filename: str = ""
    _normalized_task: dict[str, Any] | _MISSING_TYPE = field(init=False, repr=False)
    error: MatchError | None = None
    position: Any = None

    @property
    def name(self) -> str | None:
        """Return the name of the task."""
        name = self.raw_task.get("name", None)
        if name is not None and not isinstance(name, str):
            msg = "Task name can only be a string."
            raise RuntimeError(msg)
        return name

    @property
    def action(self) -> str:
        """Return the resolved action name."""
        action_name = self.normalized_task["action"]["__ansible_module_original__"]
        if not isinstance(action_name, str):
            msg = "Task actions can only be strings."
            raise TypeError(msg)
        return action_name

    @property
    def args(self) -> Any:
        """Return the arguments passed to the task action.

        While we usually expect to return a dictionary, it can also
        return a templated string when jinja is used.
        """
        if "args" in self.raw_task:
            return self.raw_task["args"]
        result = {}
        for k, v in self.normalized_task["action"].items():
            if k not in ANNOTATION_KEYS:
                result[k] = v
        return result

    @property
    def normalized_task(self) -> dict[str, Any]:
        """Return the name of the task."""
        if not hasattr(self, "_normalized_task"):
            try:
                self._normalized_task = normalize_task(
                    self.raw_task,
                    filename=self.filename,
                )
            except MatchError as err:
                self.error = err
                # When we cannot normalize it, we just use the raw task instead
                # to avoid adding extra complexity to the rules.
                self._normalized_task = self.raw_task
        if isinstance(self._normalized_task, _MISSING_TYPE):
            msg = "Task was not normalized"
            raise TypeError(msg)
        return self._normalized_task

    @property
    def skip_tags(self) -> list[str]:
        """Return the list of tags to skip."""
        skip_tags: list[str] = self.raw_task.get(SKIPPED_RULES_KEY, [])
        return skip_tags

    def is_handler(self) -> bool:
        """Return true for tasks that are handlers."""
        is_handler_file = False
        if isinstance(self._normalized_task, dict):
            file_name = str(self._normalized_task["action"].get(FILENAME_KEY, None))
            if file_name:
                is_handler_file = "handlers" in str(file_name)
        return is_handler_file if is_handler_file else ".handlers[" in self.position

    def __repr__(self) -> str:
        """Return a string representation of the task."""
        return f"Task('{self.name}' [{self.position}])"

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the task."""
        return self.normalized_task.get(key, default)

    def __getitem__(self, index: str) -> Any:
        """Allow access as task[...]."""
        return self.normalized_task[index]

    def __iter__(self) -> Iterator[str]:
        """Provide support for 'key in task'."""
        yield from (f for f in self.normalized_task)


def task_in_list(
    data: AnsibleBaseYAMLObject,
    file: Lintable,
    kind: str,
    position: str = ".",
) -> Iterator[Task]:
    """Get action tasks from block structures."""

    def each_entry(data: AnsibleBaseYAMLObject, position: str) -> Iterator[Task]:
        if not data:
            return
        for entry_index, entry in enumerate(data):
            if not entry:
                continue
            _pos = f"{position}[{entry_index}]"
            if isinstance(entry, dict):
                yield Task(
                    entry,
                    position=_pos,
                )
            for block in [k for k in entry if k in NESTED_TASK_KEYS]:
                yield from task_in_list(
                    data=entry[block],
                    file=file,
                    kind="tasks",
                    position=f"{_pos}.{block}",
                )

    if not isinstance(data, list):
        return
    if kind == "playbook":
        attributes = ["tasks", "pre_tasks", "post_tasks", "handlers"]
        for item_index, item in enumerate(data):
            for attribute in attributes:
                if not isinstance(item, dict):
                    continue
                if attribute in item:
                    if isinstance(item[attribute], list):
                        yield from each_entry(
                            item[attribute],
                            f"{position }[{item_index}].{attribute}",
                        )
                    elif item[attribute] is not None:
                        msg = f"Key '{attribute}' defined, but bad value: '{item[attribute]!s}'"
                        raise RuntimeError(msg)
    else:
        yield from each_entry(data, position)


def add_action_type(actions: AnsibleBaseYAMLObject, action_type: str) -> list[Any]:
    """Add action markers to task objects."""
    results = []
    for action in actions:
        # ignore empty task
        if not action:
            continue
        action["__ansible_action_type__"] = BLOCK_NAME_TO_ACTION_TYPE_MAP[action_type]
        results.append(action)
    return results


def get_action_tasks(data: AnsibleBaseYAMLObject, file: Lintable) -> list[Any]:
    """Get a flattened list of action tasks from the file."""
    tasks = []
    if file.kind in ["tasks", "handlers"]:
        tasks = add_action_type(data, file.kind)
    else:
        tasks.extend(extract_from_list(data, PLAYBOOK_TASK_KEYWORDS))

    # Add sub-elements of block/rescue/always to tasks list
    tasks.extend(extract_from_list(tasks, NESTED_TASK_KEYS, recursive=True))

    return tasks


@cache
def parse_yaml_linenumbers(
    lintable: Lintable,
) -> AnsibleBaseYAMLObject:
    """Parse yaml as ansible.utils.parse_yaml but with linenumbers.

    The line numbers are stored in each node's LINE_NUMBER_KEY key.
    """
    result = []

    def compose_node(parent: yaml.nodes.Node, index: int) -> yaml.nodes.Node:
        # the line number where the previous token has ended (plus empty lines)
        line = loader.line
        node = Composer.compose_node(loader, parent, index)
        if not isinstance(node, yaml.nodes.Node):
            msg = "Unexpected yaml data."
            raise TypeError(msg)
        node.__line__ = line + 1  # type: ignore[attr-defined]
        return node

    def construct_mapping(
        node: AnsibleBaseYAMLObject,
        *,
        deep: bool = False,
    ) -> AnsibleMapping:
        mapping = AnsibleConstructor.construct_mapping(loader, node, deep=deep)
        if hasattr(node, "__line__"):
            mapping[LINE_NUMBER_KEY] = node.__line__
        else:
            mapping[LINE_NUMBER_KEY] = mapping._line_number  # noqa: SLF001
        mapping[FILENAME_KEY] = lintable.path
        return mapping

    try:
        kwargs = {}
        if "vault_password" in inspect.getfullargspec(AnsibleLoader.__init__).args:
            kwargs["vault_password"] = DEFAULT_VAULT_PASSWORD
        loader = AnsibleLoader(lintable.content, **kwargs)
        loader.compose_node = compose_node
        loader.construct_mapping = construct_mapping
        # while Ansible only accepts single documents, we also need to load
        # multi-documents, as we attempt to load any YAML file, not only
        # Ansible managed ones.
        while True:
            data = loader.get_data()
            if data is None:
                break
            result.append(data)
    except (
        yaml.parser.ParserError,
        yaml.scanner.ScannerError,
        yaml.constructor.ConstructorError,
        ruamel.yaml.parser.ParserError,
    ) as exc:
        msg = f"Failed to load YAML file: {lintable.path}"
        raise RuntimeError(msg) from exc

    if len(result) == 0:
        return None  # empty documents
    if len(result) == 1:
        return result[0]
    return result


def get_cmd_args(task: dict[str, Any]) -> str:
    """Extract the args from a cmd task as a string."""
    if "cmd" in task["action"]:
        args = task["action"]["cmd"]
    else:
        args = task["action"].get("_raw_params", [])
    if not isinstance(args, str):
        return " ".join(args)
    return args


def get_first_cmd_arg(task: dict[str, Any]) -> Any:
    """Extract the first arg from a cmd task."""
    try:
        first_cmd_arg = get_cmd_args(task).split()[0]
    except IndexError:
        return None
    return first_cmd_arg


def get_second_cmd_arg(task: dict[str, Any]) -> Any:
    """Extract the second arg from a cmd task."""
    try:
        second_cmd_arg = get_cmd_args(task).split()[1]
    except IndexError:
        return None
    return second_cmd_arg


def is_playbook(filename: str) -> bool:
    """Check if the file is a playbook.

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
    except Exception as exc:  # pylint: disable=broad-except # noqa: BLE001
        _logger.warning(
            "Failed to load %s with %s, assuming is not a playbook.",
            filename,
            exc,
        )
    else:
        if (
            isinstance(f, AnsibleSequence)
            and hasattr(next(iter(f), {}), "keys")
            and playbooks_keys.intersection(next(iter(f), {}).keys())
        ):
            return True
    return False


def get_lintables(
    opts: Options = options,
    args: list[str] | None = None,
) -> list[Lintable]:
    """Detect files and directories that are lintable."""
    lintables: list[Lintable] = []

    # passing args bypass auto-detection mode
    if args:
        for arg in args:
            lintable = Lintable(arg)
            lintables.append(lintable)
    else:
        for filename in discover_lintables(opts):
            path = Path(filename)
            lintables.append(Lintable(path))

        # stage 2: guess roles from current lintables, as there is no unique
        # file that must be present in any kind of role.
        _extend_with_roles(lintables)

    return lintables


def _extend_with_roles(lintables: list[Lintable]) -> None:
    """Detect roles among lintables and adds them to the list."""
    for lintable in lintables:
        parts = lintable.path.parent.parts
        if "roles" in parts:
            role = lintable.path
            while role.parent.name != "roles" and role.name:
                role = role.parent
            if role.exists() and not role.is_file():
                lintable = Lintable(role)
                if lintable.kind == "role" and lintable not in lintables:
                    _logger.debug("Added role: %s", lintable)
                    lintables.append(lintable)


def convert_to_boolean(value: Any) -> bool:
    """Use Ansible to convert something to a boolean."""
    return bool(boolean(value))


def parse_examples_from_plugin(lintable: Lintable) -> tuple[int, str]:
    """Parse yaml inside plugin EXAMPLES string.

    Store a line number offset to realign returned line numbers later
    """
    offset = 1
    parsed = ast.parse(lintable.content)
    for child in parsed.body:
        if isinstance(child, ast.Assign):
            label = child.targets[0]
            if isinstance(label, ast.Name) and label.id == "EXAMPLES":
                offset = child.lineno - 1
                break

    docs = read_docstring(str(lintable.path))
    examples = docs["plainexamples"]

    # Ignore the leading newline and lack of document start
    # as including those in EXAMPLES would be weird.
    return offset, (f"---{examples}" if examples else "")


@lru_cache
def load_plugin(name: str) -> PluginLoadContext:
    """Return loaded ansible plugin/module."""
    loaded_module = action_loader.find_plugin_with_context(
        name,
        ignore_deprecated=True,
        check_aliases=True,
    )
    if not loaded_module.resolved:
        loaded_module = module_loader.find_plugin_with_context(
            name,
            ignore_deprecated=True,
            check_aliases=True,
        )
    if not loaded_module.resolved and name.startswith("ansible.builtin."):
        # fallback to core behavior of using legacy
        loaded_module = module_loader.find_plugin_with_context(
            name.replace("ansible.builtin.", "ansible.legacy."),
            ignore_deprecated=True,
            check_aliases=True,
        )
    return loaded_module
