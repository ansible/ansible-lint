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
import collections.abc
import contextlib
import copy
import inspect
import logging
import os
import re
from collections.abc import (
    ItemsView,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from dataclasses import _MISSING_TYPE, dataclass, field
from functools import cache, lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import ruamel.yaml.parser
import yaml
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_bytes
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.mod_args import ModuleArgsParser
from ansible.parsing.plugin_docs import read_docstring
from ansible.parsing.splitter import split_args
from ansible.parsing.vault import PromptVaultSecret
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.plugins.loader import (
    PluginLoadContext,
    action_loader,
    add_all_plugin_dirs,
    module_loader,
)
from ansible.template import Templar
from ansible.utils.collection_loader import AnsibleCollectionConfig
from jinja2 import Environment, nodes
from jinja2.exceptions import TemplateError, TemplateSyntaxError
from packaging.version import Version
from yaml.composer import Composer
from yaml.parser import ParserError
from yaml.representer import RepresenterError
from yaml.scanner import ScannerError

from ansiblelint._internal.rules import AnsibleParserErrorRule, RuntimeErrorRule
from ansiblelint.app import App, get_app
from ansiblelint.config import Options, get_deps_versions, options
from ansiblelint.constants import (
    ANNOTATION_KEYS,
    FILENAME_KEY,
    INCLUSION_ACTION_NAMES,
    LINE_NUMBER_KEY,
    NESTED_TASK_KEYS,
    ROLE_IMPORT_ACTION_NAMES,
    SKIPPED_RULES_KEY,
    FileType,
)
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable, discover_lintables
from ansiblelint.skip_utils import is_nested_task
from ansiblelint.text import has_jinja, is_fqcn, removeprefix
from ansiblelint.types import (
    AnsibleBaseYAMLObject,  # pyright: ignore[reportAttributeAccessIssue]
    AnsibleConstructor,  # pyright: ignore[reportAttributeAccessIssue]
    AnsibleJSON,
    AnsibleMapping,  # pyright: ignore[reportAttributeAccessIssue]
    AnsibleSequence,  # pyright: ignore[reportAttributeAccessIssue]
    TrustedAsTemplate,
)

if TYPE_CHECKING:
    from ansiblelint.rules import RulesCollection
# ansible-lint doesn't need/want to know about encrypted secrets, so we pass a
# string as the password to enable such yaml files to be opened and parsed
# successfully.
DEFAULT_VAULT_PASSWORD = "x"  # noqa: S105

PLAYBOOK_DIR = os.environ.get("ANSIBLE_PLAYBOOK_DIR", None)
LINE_COLUMN_REGEX = re.compile(
    r".*line (?P<line>\d+), column (?P<column>\d+).*", flags=re.MULTILINE
)


_logger = logging.getLogger(__name__)


def parse_yaml_from_file(filepath: str) -> AnsibleJSON:
    """Extract a decrypted YAML object from file."""
    dataloader = DataLoader()  # type: ignore[no-untyped-call]
    if hasattr(dataloader, "set_vault_secrets"):
        dataloader.set_vault_secrets([
            ("default", PromptVaultSecret(_bytes=to_bytes(DEFAULT_VAULT_PASSWORD)))  # type: ignore[no-untyped-call]
        ])
    result: object = dataloader.load_from_file(filepath)
    if result is None:
        return result
    if isinstance(result, AnsibleJSON):
        return result
    # pragma: no cover
    msg = "Expected a YAML object"
    raise TypeError(msg)


def path_dwim(basedir: str, given: str) -> str:
    """Convert a given path do-what-I-mean style."""
    dataloader = DataLoader()  # type: ignore[no-untyped-call]
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

    dataloader = DataLoader()  # type: ignore[no-untyped-call]
    dataloader.set_basedir(str(basedir))
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


def has_lookup_function_calls(varname: str) -> bool:
    """Check if a template string contains lookup, query, or q function calls using AST parsing.

    This function parses Jinja2 templates and looks for function calls to
    'lookup', 'query', or 'q' by examining the AST).

    :param varname: The template string to analyze
    :return: True if lookup functions are found, False otherwise
    """
    lookup_names = {"lookup", "query", "q"}

    try:
        env = Environment(autoescape=True)
        ast_tree = env.parse(varname)

        for node in ast_tree.find_all(nodes.Call):
            if isinstance(node.node, nodes.Name) and node.node.name in lookup_names:
                return True
    except (TemplateSyntaxError, TemplateError, AttributeError):
        # Fallback to regex for edge cases where Jinja2 parsing fails
        fallback_pattern = re.compile(r"\(?(lookup|query|q)\)?\s*\(")
        return bool(fallback_pattern.search(varname))
    else:
        return False


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
    ansible_core_2_19 = Version("2.19")
    deps = get_deps_versions()

    # Skip lookups for ansible-core >= 2.19; use disable_lookups for older versions
    if has_lookup_function_calls(str(varname)):
        if deps["ansible-core"] and deps["ansible-core"] >= ansible_core_2_19:
            return varname
        kwargs["disable_lookups"] = True

    for _i in range(10):
        try:
            if TrustedAsTemplate and not isinstance(varname, TrustedAsTemplate):
                varname = TrustedAsTemplate().tag(varname)
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

                v = templar.environment.filters
                if not hasattr(v, "_delegatee"):  # pragma: no cover
                    raise
                v._delegatee[missing_filter] = mock_filter  # fmt: skip # noqa: SLF001 # pyright: ignore[reportAttributeAccessIssue]
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


def tokenize(value: str) -> tuple[list[str], dict[str, str]]:
    """Parse a string task invocation."""
    # We do not try to tokenize something very simple because it would fail to
    # work for a case like: task_include: path with space.yml
    if value and "=" not in value:
        return ([value], {})

    parts = split_args(value)  # type: ignore[no-untyped-call]
    args: list[str] = []
    kwargs: dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            args.append(part)
        else:
            k, v = part.split("=", 1)
            kwargs[k] = v
    return (args, kwargs)


def playbook_items(pb_data: AnsibleJSON) -> ItemsView:  # type: ignore[type-arg]
    """Return a list of items from within the playbook."""
    if isinstance(pb_data, dict):
        return pb_data.items()
    # "if play" prevents failure if the play sequence contains None,
    # which is weird but currently allowed by Ansible
    # https://github.com/ansible/ansible-lint/issues/849
    if isinstance(pb_data, Sequence):
        return [
            item
            for play in pb_data
            if isinstance(play, Mapping)
            for item in play.items()
        ]  # type: ignore[return-value]

    return {}.items()


def set_collections_basedir(basedir: Path) -> None:
    """Set the playbook directory as playbook_paths for the collection loader."""
    # Ansible expects only absolute paths inside `playbook_paths` and will
    # produce weird errors if we use a relative one.
    # https://github.com/psf/black/issues/4519
    # fmt: off
    AnsibleCollectionConfig.playbook_paths = (  # pyright: ignore[reportAttributeAccessIssue]
        str(basedir.resolve()))
    # fmt: on


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
    except (AnsibleError, ValueError, RepresenterError, ImportError):
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
        lintable: Lintable,
        k: str,
        v: Any,
        parent_type: FileType,
    ) -> list[Lintable]:
        """Include children."""
        basedir = str(lintable.path.parent)

        # handle special case include_tasks: name=filename.yml
        if k in INCLUSION_ACTION_NAMES and isinstance(v, dict) and "file" in v:
            v = v["file"]

        # we cannot really parse any jinja2 in includes, so we ignore them
        if not v or not isinstance(v, str) or "{{" in v:
            return []

        # handle include: filename.yml tags=blah
        (args, kwargs) = tokenize(v)

        if args:
            file = args[0]
        elif "file" in kwargs:
            file = kwargs["file"]
        else:
            return []

        result = path_dwim(basedir, file)
        while basedir not in ["", "/"]:
            if os.path.exists(result):
                break
            basedir = os.path.dirname(basedir)
            result = path_dwim(basedir, file)

        return [Lintable(result, kind=parent_type)]

    def taskshandlers_children(
        self,
        lintable: Lintable,
        k: str,
        v: Any | None,
        parent_type: FileType,
    ) -> list[Lintable]:
        """TasksHandlers Children."""
        basedir = str(lintable.path.parent)
        results: list[Lintable] = []
        if v is None or isinstance(v, int | str):
            raise MatchError(
                message="A malformed block was encountered while loading a block.",
                rule=RuntimeErrorRule(),
                lintable=lintable,
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
                task_handler = normalize_task_v2(
                    Task(task_handler, filename=str(lintable.path)),
                )
                self._validate_task_handler_action_for_role(task_handler["action"])
                name = task_handler["action"].get("name")
                if has_jinja(name):
                    # we cannot deal with dynamic imports
                    continue
                results.extend(
                    self.roles_children(lintable, k, [name], parent_type),
                )
                continue

            if "block" not in task_handler:
                continue

            for elem in ("block", "rescue", "always"):
                if elem in task_handler:
                    results.extend(
                        self.taskshandlers_children(
                            lintable,
                            k,
                            task_handler[elem],
                            parent_type,
                        ),
                    )

        return results

    def _validate_task_handler_action_for_role(self, th_action: dict[str, Any]) -> None:
        """Verify that the task handler action is valid for role include."""
        module = th_action["__ansible_module__"]

        lintable = Lintable(
            self.rules.options.lintables[0] if self.rules.options.lintables else ".",
        )
        if "name" not in th_action:
            raise MatchError(
                message=f"Failed to find required 'name' key in {module!s}",
                rule=self.rules.rules[0],
                lintable=lintable,
            )

        if not isinstance(th_action["name"], str):
            raise MatchError(
                message=f"Value assigned to 'name' key on '{module!s}' is not a string.",
                rule=self.rules.rules[1],
                lintable=lintable,
            )

    def roles_children(
        self,
        lintable: Lintable,
        k: str,
        v: Sequence[Any],
        parent_type: FileType,
    ) -> list[Lintable]:
        """Roles children."""
        # pylint: disable=unused-argument # parent_type)
        basedir = str(lintable.path.parent)
        results: list[Lintable] = []
        if not v or not isinstance(v, Iterable):
            # typing does not prevent junk from being passed in
            return results
        for role in v:
            if isinstance(role, dict):
                if "role" in role or "name" in role:
                    if "tags" not in role or "skip_ansible_lint" not in role["tags"]:
                        role_name = role.get("role", role.get("name"))
                        if not isinstance(role_name, str):  # pragma: no cover
                            msg = "Role name is not a string."
                            raise TypeError(msg)
                        results.extend(
                            self._look_for_role_files(
                                basedir,
                                role_name,
                            ),
                        )
                elif k != "dependencies":
                    msg = f'role dict {role} does not contain a "role" or "name" key'
                    raise SystemExit(msg)
            else:
                results.extend(self._look_for_role_files(basedir, role))
        return results

    def import_playbook_children(
        self,
        lintable: Lintable,
        k: str,  # pylint: disable=unused-argument
        v: Any,
        parent_type: FileType,
    ) -> list[Lintable]:
        """Include import_playbook children."""

        def append_playbook_path(loc: str, playbook_path: list[str]) -> None:
            possible_paths.append(
                Path(
                    path_dwim(
                        os.path.expanduser(loc),
                        os.path.join(
                            "ansible_collections",
                            namespace_name,
                            collection_name,
                            "playbooks",
                            *playbook_path,
                        ),
                    ),
                ),
            )

        # import_playbook only accepts a string as argument (no dict syntax)
        if not isinstance(v, str):
            return []

        possible_paths = []
        namespace_name, collection_name, *playbook_path = parse_fqcn(v)
        if namespace_name and collection_name:
            for loc in self.app.runtime.config.collections_paths:
                append_playbook_path(
                    loc,
                    [*playbook_path[:-1], f"{playbook_path[-1]}.yml"],
                )
                append_playbook_path(
                    loc,
                    [*playbook_path[:-1], f"{playbook_path[-1]}.yaml"],
                )
        else:
            possible_paths.append(lintable.path.parent / v)

        for possible_path in possible_paths:
            if not possible_path.exists():
                msg = f"Failed to find {v} playbook."
            elif not self.app.runtime.has_playbook(
                str(possible_path),
            ):
                msg = f"Failed to load {v} playbook due to failing syntax check."
                break
            elif namespace_name and collection_name:
                # don't lint foreign playbook
                return []
            else:
                return [Lintable(possible_path, kind=parent_type)]

        _logger.error(msg)
        return []

    def _look_for_role_files(self, basedir: str, role: str) -> list[Lintable]:
        role_path = self._rolepath(basedir, role)
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

    def _rolepath(self, basedir: str, role: str) -> str | None:
        role_path = None
        namespace_name, collection_name, *role_name = parse_fqcn(role)

        possible_paths = [
            # if included from a playbook
            path_dwim(basedir, os.path.join("roles", role_name[-1])),
            path_dwim(basedir, role_name[-1]),
            # if included from roles/[role]/meta/main.yml
            path_dwim(basedir, os.path.join("..", "..", "..", "roles", role_name[-1])),
            path_dwim(basedir, os.path.join("..", "..", role_name[-1])),
            # if checking a role in the current directory
            path_dwim(basedir, os.path.join("..", role_name[-1])),
        ]
        if len(role_name) > 1:
            # This ignores deeper structures than 1 level
            possible_paths.append(path_dwim(basedir, os.path.join("roles", *role_name)))
            possible_paths.append(path_dwim(basedir, os.path.join(*role_name)))
            possible_paths.append(
                path_dwim(basedir, os.path.join("..", "..", *role_name))
            )

        for loc in self.app.runtime.config.default_roles_path:
            loc = os.path.expanduser(loc)
            possible_paths.append(path_dwim(loc, role_name[-1]))

        if namespace_name and collection_name:
            for loc in get_app(cached=True).runtime.config.collections_paths:
                loc = os.path.expanduser(loc)
                possible_paths.append(
                    path_dwim(
                        loc,
                        os.path.join(
                            "ansible_collections",
                            namespace_name,
                            collection_name,
                            "roles",
                            role_name[-1],
                        ),
                    ),
                )

        possible_paths.append(path_dwim(basedir, ""))

        for path_option in possible_paths:  # pragma: no branch
            if os.path.isdir(path_option):
                role_path = path_option
                break

        if role_path:  # pragma: no branch
            add_all_plugin_dirs(role_path)  # type: ignore[no-untyped-call]

        return role_path


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

            file_name = ""
            action_args = task_handler[task_handler_key]
            if isinstance(action_args, str):
                (args, kwargs) = tokenize(action_args)
                if len(args) == 1:
                    file_name = args[0]
                elif kwargs.get("file", None):
                    file_name = kwargs["file"]
                else:
                    # ignore invalid data (syntax check will outside the scope)
                    continue

            if isinstance(action_args, Mapping) and action_args.get("file", None):
                file_name = action_args["file"]

            if not file_name:
                # ignore invalid data (syntax check will outside the scope)
                continue
            f = path_dwim(basedir, file_name)
            while basedir not in ["", "/"]:
                if os.path.exists(f):
                    break
                basedir = os.path.dirname(basedir)
                f = path_dwim(basedir, file_name)
            return Lintable(f, kind=child_type)
    msg = f"The node contains none of: {', '.join(sorted(INCLUSION_ACTION_NAMES))}"
    raise LookupError(msg)


def _sanitize_task(task: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Return a stripped-off task structure compatible with new Ansible.

    This helper takes a copy of the incoming task and drops
    any internally used keys from it.
    """
    result = copy.deepcopy(task)
    # task is an AnsibleMapping which inherits from OrderedDict, so we need
    # to use `del` to remove unwanted keys.

    def remove_keys(obj: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        """Recursively removes specified keys from a nested dictionary or list.

        :param obj: The input dictionary or list to process.
        :param forbidden_keys: List of keys to remove from dictionaries.
        :return: A new object with forbidden keys removed.
        """
        if isinstance(obj, MutableMapping):
            for key in [SKIPPED_RULES_KEY, FILENAME_KEY, LINE_NUMBER_KEY]:
                if key in obj:
                    del obj[key]
            for value in obj.values():
                if isinstance(value, MutableMapping):
                    remove_keys(value)

        return obj  # Base case: return non-dict, non-list values unchanged

    return remove_keys(result)


def _extract_ansible_parsed_keys_from_task(
    result: MutableMapping[str, Any],
    task: MutableMapping[str, Any],
    keys: tuple[str, ...],
) -> MutableMapping[str, Any]:
    """Return a dict with existing key in task."""
    for k, v in list(task.items()):
        if k in keys:
            # we don't want to re-assign these values, which were
            # determined by the ModuleArgsParser() above
            continue
        result[k] = v
    return result


def normalize_task_v2(task: Task) -> MutableMapping[str, Any]:
    """Ensure tasks have a normalized action key and strings are converted to python objects."""
    raw_task = task.raw_task
    result: MutableMapping[str, Any] = {}
    ansible_parsed_keys = ("action", "local_action", "args", "delegate_to")
    arguments = {}

    if is_nested_task(raw_task):
        _extract_ansible_parsed_keys_from_task(result, raw_task, ansible_parsed_keys)
        # Add dummy action for block/always/rescue statements
        result["action"] = {
            "__ansible_module__": "block/always/rescue",
            "__ansible_module_original__": "block/always/rescue",
        }

        return result

    sanitized_task = _sanitize_task(raw_task)
    mod_arg_parser = ModuleArgsParser(sanitized_task)  # type: ignore[no-untyped-call]

    try:
        action, arguments, result["delegate_to"] = mod_arg_parser.parse(  # type: ignore[no-untyped-call]
            skip_action_validation=options.skip_action_validation,
        )
    except AnsibleParserError as exc:  # pragma: no cover
        if "get_line_column" not in globals():
            from ansiblelint.yaml_utils import get_line_column
        # pylint: disable=possibly-used-before-assignment
        line, column = get_line_column(raw_task, 0)
        if not line:
            line = 0
            column = 0
            regex = LINE_COLUMN_REGEX.search(exc.message)
            if regex:
                line = int(regex.group("line"))
                column = int(regex.group("column"))
        if not exc.message.startswith(
            "Complex args containing variables cannot use bare variables"
        ):
            raise MatchError(
                rule=AnsibleParserErrorRule(),
                message=exc.message,
                lintable=Lintable(task.filename or ""),
                lineno=line or 1,
                column=column or None,
            ) from exc
        result = sanitized_task
        if "action" not in result:
            msg = "Unable to normalize task"
            raise NotImplementedError(msg) from exc
        action = result["action"]

    # denormalize shell -> command conversion
    if "_uses_shell" in arguments:
        action = "shell"
        del arguments["_uses_shell"]

    _extract_ansible_parsed_keys_from_task(
        result,
        raw_task,
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
    # Inject back original line number information into the task
    if (
        action_unnormalized in task.raw_task
        and isinstance(task.raw_task[action_unnormalized], Mapping)
        and "__line__" in task.raw_task[action_unnormalized]
    ):
        result["action"]["__line__"] = task.raw_task[action_unnormalized]["__line__"]

    result["action"].update(arguments)
    return result


# pylint: disable=too-many-nested-blocks
def extract_from_list(  # type: ignore[no-any-unimported]
    blocks: AnsibleBaseYAMLObject,
    candidates: list[str],
    *,
    recursive: bool = False,
) -> list[Any]:
    """Get action tasks from block structures."""
    results: list[Any] = []
    if isinstance(blocks, Iterable):
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
class Task(Mapping[str, Any]):
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
    position:
        The position of the task in the data structure using JSONPath like
        notation (no $ prefix).
    """

    raw_task: MutableMapping[str, Any]
    filename: str = ""
    _normalized_task: MutableMapping[str, Any] | _MISSING_TYPE = field(
        init=False, repr=False
    )
    error: MatchError | None = None
    position: str = ""
    kind: str = "tasks"

    def __post_init__(self) -> None:
        """Ensures that the task is valid."""
        # This command ensures that we can print the task, ensuring that we
        # fail fast if someone tries to instantiate an invalid task.
        str(self)

    def __len__(self) -> int:
        """Return the length of the normalized task."""
        return len(self.normalized_task)

    @property
    def name(self) -> str | None:
        """Return the name of the task."""
        name = self.raw_task.get("name", None)
        if name is not None and not isinstance(name, str):  # pragma: no cover
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
        result = {
            k: v
            for k, v in self.normalized_task["action"].items()
            if k not in ANNOTATION_KEYS
        }
        return result

    @property
    def normalized_task(self) -> MutableMapping[str, Any]:
        """Return the name of the task."""
        if not hasattr(self, "_normalized_task"):
            try:
                self._normalized_task = self._normalize_task()
            except MatchError as err:
                self.error = err
                # When we cannot normalize it, we just use the raw task instead
                # to avoid adding extra complexity to the rules.
                self._normalized_task = self.raw_task
        if isinstance(self._normalized_task, _MISSING_TYPE):
            msg = "Task was not normalized"
            raise TypeError(msg)
        return self._normalized_task

    def _normalize_task(self) -> MutableMapping[str, Any]:
        """Unify task-like object structures."""
        ansible_action_type = self.raw_task.get("__ansible_action_type__", "task")
        if "__ansible_action_type__" in self.raw_task:
            del self.raw_task["__ansible_action_type__"]  # pragma: no cover
        task = normalize_task_v2(self)
        task[FILENAME_KEY] = self.filename
        task["__ansible_action_type__"] = ansible_action_type
        return task

    @property
    def skip_tags(self) -> list[str]:
        """Return the list of tags to skip."""
        skip_tags: list[str] = self.raw_task.get(SKIPPED_RULES_KEY, [])
        return skip_tags

    def is_handler(self) -> bool:
        """Return true for tasks that are handlers."""
        return self.kind == "handlers"

    def __str__(self) -> str:
        """Return a string representation of the task."""
        name = self.get("name")
        if name:
            return str(name)
        action = self.get("action")
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

        raw_params = action.get("_raw_params", [])
        if isinstance(raw_params, list):
            for item in raw_params:
                args.extend(str(item))
        else:
            args.append(raw_params)
        result = f"{action['__ansible_module__']} {' '.join(args)}"
        return result

    def __repr__(self) -> str:
        """Return a string representation of the task."""
        result = f"Task('{self.name or self.action}'"
        if self.position:
            result += f" [{self.position}])"
        result += ")"
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the task."""
        return self.normalized_task.get(key, default)

    def __getitem__(self, index: str) -> Any:
        """Allow access as task[...]."""
        return self.normalized_task[index]

    def __iter__(self) -> Iterator[str]:
        """Provide support for 'key in task'."""
        yield from (f for f in self.normalized_task)

    @property
    def line(self) -> int:
        """Return the line number of the task."""
        result: int = 0
        if "get_line_column" not in globals():
            from ansiblelint.yaml_utils import get_line_column
        result, _ = get_line_column(self.raw_task)  # pylint: disable=possibly-used-before-assignment
        if not result:  # pragma: no cover
            x = self.get("action", {})
            result = int(x.get(LINE_NUMBER_KEY, 0))
        return result or 1

    def get_error_line(self, path: list[str | int]) -> int:
        """Return error line number."""
        ctx: Mapping[Any, Any] = self.normalized_task
        line = 1
        if LINE_NUMBER_KEY in self.normalized_task:
            line = self.normalized_task[LINE_NUMBER_KEY]
        for _ in path:
            if (
                isinstance(ctx, collections.abc.Container) and _ in ctx
            ):  # isinstance(ctx, collections.abc.Container) and
                value = ctx.get(  # pyright: ignore[reportAttributeAccessIssue]
                    _  # pyright: ignore[reportArgumentType]
                )
                if isinstance(value, Mapping):
                    ctx = value
                if (
                    isinstance(ctx, collections.abc.Container)
                    and LINE_NUMBER_KEY in ctx
                ):
                    line = ctx[LINE_NUMBER_KEY]  # pyright: ignore[reportIndexIssue]
        if not isinstance(line, int):  # pragma: no cover
            msg = "Line number is not an integer"
            raise TypeError(msg)
        return line


def task_in_list(  # type: ignore[no-any-unimported]
    data: AnsibleBaseYAMLObject,
    file: Lintable,
    kind: str,
    position: str = ".",
) -> Iterator[Task]:
    """Get action tasks from block structures."""

    def each_entry(  # type: ignore[no-any-unimported]
        data: Sequence[Any] | AnsibleMapping, file: Lintable, kind: str, position: str
    ) -> Iterator[Task]:
        if not data or not isinstance(data, Iterable):
            return
        for entry_index, entry in enumerate(data):
            if not entry:
                continue
            pos_ = f"{position}[{entry_index}]"
            if isinstance(entry, MutableMapping):
                yield Task(
                    entry,
                    filename=file.filename,
                    kind=kind,
                    position=pos_,
                )
            for block in [k for k in entry if k in NESTED_TASK_KEYS]:
                v = entry[block]
                if isinstance(v, AnsibleBaseYAMLObject):
                    yield from task_in_list(
                        data=v,
                        file=file,
                        kind=kind,
                        position=f"{pos_}.{block}",
                    )

    if not isinstance(data, Sequence):
        return
    if kind == "playbook":
        attributes = ["tasks", "pre_tasks", "post_tasks", "handlers"]
        for item_index, item in enumerate(data):
            for attribute in attributes:
                if not isinstance(item, Mapping):
                    continue
                if attribute in item:
                    if isinstance(item[attribute], Sequence):
                        yield from each_entry(
                            item[attribute],
                            file=file,
                            kind="tasks" if "tasks" in attribute else "handlers",
                            position=f"{position}[{item_index}].{attribute}",
                        )
                    elif item[attribute] is not None:  # pragma: no cover
                        msg = f"Key '{attribute}' defined, but bad value: '{item[attribute]!s}'"
                        raise RuntimeError(msg)
    elif isinstance(data, Sequence):
        yield from each_entry(data, file=file, position=position, kind=kind)


def add_action_type(  # type: ignore[no-any-unimported]
    actions: AnsibleBaseYAMLObject, action_type: str
) -> AnsibleSequence:
    """Add action markers to task objects."""
    results = AnsibleSequence()
    if isinstance(actions, Iterable):
        for action in actions:
            # ignore empty task
            if not action or isinstance(action, str):  # pragma: no cover
                continue
            action["__ansible_action_type__"] = BLOCK_NAME_TO_ACTION_TYPE_MAP[
                action_type
            ]
            results.append(action)
    return results


@cache
def parse_yaml_linenumbers(  # type: ignore[no-any-unimported]
    lintable: Lintable,
) -> AnsibleBaseYAMLObject | None:
    """Parse yaml as ansible.utils.parse_yaml but with linenumbers.

    The line numbers are stored in each node's LINE_NUMBER_KEY key.
    """
    loader: AnsibleLoader  # type: ignore[valid-type]
    result = AnsibleSequence()

    # signature of Composer.compose_node
    def compose_node(parent: yaml.nodes.Node | None, index: int) -> yaml.nodes.Node:
        # the line number where the previous token has ended (plus empty lines)
        node = Composer.compose_node(loader, parent, index)  # type: ignore[no-untyped-call,arg-type,unused-ignore]
        if not isinstance(node, yaml.nodes.Node):
            msg = "Unexpected yaml data."
            raise TypeError(msg)
        if hasattr(loader, "line"):  # pragma: no cover
            line = loader.line  # type: ignore[attr-defined]
            node.__line__ = line + 1  # type: ignore[attr-defined]
        return node

    # signature of AnsibleConstructor.construct_mapping
    def construct_mapping(  # type: ignore[no-any-unimported]
        node: yaml.MappingNode,
        deep: bool = False,  # noqa: FBT002
    ) -> AnsibleMapping:
        # pyright: ignore[reportArgumentType]
        mapping: AnsibleMapping = AnsibleConstructor.construct_mapping(  # type: ignore[no-any-unimported]
            loader, node, deep=deep
        )
        if hasattr(node, LINE_NUMBER_KEY):
            mapping[LINE_NUMBER_KEY] = getattr(node, LINE_NUMBER_KEY)
        else:
            if hasattr(mapping, "_line_number"):
                mapping[LINE_NUMBER_KEY] = mapping._line_number  # noqa: SLF001
        mapping[FILENAME_KEY] = lintable.path
        return mapping

    try:
        kwargs = {}
        if "vault_password" in inspect.getfullargspec(AnsibleLoader.__init__).args:
            kwargs["vault_password"] = DEFAULT_VAULT_PASSWORD
        # WARNING: 'unused-ignore' is needed below in order to allow mypy to
        # be passing with both pre-2.19 and post-2.19 versions of Ansible core.
        loader = AnsibleLoader(lintable.content, **kwargs)
        # redefine Composer.compose_node
        loader.compose_node = compose_node  # type: ignore[attr-defined,unused-ignore]
        # redefine AnsibleConstructor.construct_mapping
        loader.construct_mapping = construct_mapping  # type: ignore[attr-defined]
        # while Ansible only accepts single documents, we also need to load
        # multi-documents, as we attempt to load any YAML file, not only
        # Ansible managed ones.
        while True:
            data = loader.get_data()  # type: ignore[attr-defined]
            if data is None:
                break
            result.append(data)
    except (
        ParserError,
        ScannerError,
        yaml.constructor.ConstructorError,
        ruamel.yaml.parser.ParserError,
    ) as exc:
        msg = "Failed to load YAML file"
        raise RuntimeError(msg, lintable.path) from exc

    if len(result) == 0:
        return None  # empty documents
    if len(result) == 1:
        if not isinstance(result[0], AnsibleBaseYAMLObject):  # pragma: no cover
            msg = "Unexpected yaml data."
            raise TypeError(msg)
        return result[0]
    return result


def get_cmd_args(task: Mapping[str, Any]) -> str:
    """Extract the args from a cmd task as a string."""
    if "cmd" in task["action"]:
        args = task["action"]["cmd"]
    else:
        args = task["action"].get("_raw_params", [])
    if not isinstance(args, str):
        return " ".join(args)
    return args


def get_first_cmd_arg(task: Task) -> Any:
    """Extract the first arg from a cmd task."""
    try:
        first_cmd_arg = get_cmd_args(task).split()[0]
    except IndexError:
        return None
    return first_cmd_arg


def get_second_cmd_arg(task: Task) -> Any:
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
        "ansible.builtin.import_playbook",
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
        # A playbook is a sequence of dictionaries that contain at least one
        # of the playbooks_keys each.
        if isinstance(f, Sequence):
            for item in f:
                if not isinstance(item, Mapping) or not playbooks_keys.intersection(
                    item.keys()
                ):
                    return False
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
    return bool(boolean(value))  # type: ignore[no-untyped-call]


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

    docs = read_docstring(str(lintable.path.resolve(strict=False)))  # type: ignore[no-untyped-call]
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
    if not loaded_module.resolved and name.startswith(
        "ansible.builtin."
    ):  # pragma: no cover
        # fallback to core behavior of using legacy
        loaded_module = module_loader.find_plugin_with_context(
            name.replace("ansible.builtin.", "ansible.legacy."),
            ignore_deprecated=True,
            check_aliases=True,
        )
    if not isinstance(loaded_module, PluginLoadContext):  # pragma: no cover
        msg = f"Failed to load plugin: {name}"
        raise TypeError(msg)
    return loaded_module


def parse_fqcn(name: str) -> tuple[str, ...]:
    """Parse name parameter into FQCN segments."""
    if not is_fqcn(name):
        return ("", "", name)

    return tuple(name.split("."))
