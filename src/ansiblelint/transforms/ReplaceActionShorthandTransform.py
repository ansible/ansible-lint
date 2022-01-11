from typing import MutableMapping, Optional, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import CommentMark
from ruamel.yaml.tokens import CommentToken

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.TaskNoActionShorthand import (
    TaskNoActionShorthand,
    FREE_FORM_MODULES,
)
from ansiblelint.transforms import Transform


class ReplaceActionShorthandTransform(Transform):
    id = "replace-action-shorthand"
    shortdesc = "Replace action shorthand with YAML args."
    description = (
        "Using ``module: arg=value`` makes debugging more difficult. "
        "This replaces the action shorthand with YAML args:\n"
        "  module:\n"
        "    arg1: value\n"
        "    arg2: 42\n"
    )
    version_added = "5.3"

    wants = TaskNoActionShorthand
    tags = TaskNoActionShorthand.tags

    def __call__(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to replace the action shorthand."""

        target_task: CommentedMap = self._seek(match.yaml_path, data)

        # see ansiblelint.utils.normalize_task()
        # semantics of which one is fqcn may change in future versions
        action: dict = match.task["action"].copy()
        # module_normalized = action.pop("__ansible_module__")
        module = action.pop("__ansible_module_original__")
        if module in FREE_FORM_MODULES:
            return

        # '__ansible_arguments__' includes _raw_params or argv
        arguments = action.pop("__ansible_arguments__")
        if arguments and isinstance(arguments, MutableMapping):
            # set_fact stores vars in _raw_params, and we want to change those tasks.
            # add_host uses _raw_params for host vars, so it is a dict there as well.
            action.update(arguments)
        elif arguments:
            # We ignore other uses of _raw_params and argv:
            #   _raw_params is for command, shell, script, include*, import*,
            #   and argv is only used by command.
            # Since we don't know how to handle these arguments. bail.
            return

        internal_keys = [k for k in action if k.startswith("__") and k.endswith("__")]
        for internal_key in internal_keys:
            del action[internal_key]

        # We can't just use the ansible-normalized values or
        # ruamel.yaml gets confused with AnsibleYAMLObjects
        commented_params = CommentedMap()
        for key, value in action.items():
            # str() to drop AnsibleUnicode
            key = str(key)
            # Ansible seems to parse all values as str. Users must fix their types.
            # Protects against int, bool, float (if Ansible were to cast to that).
            # Note: If Ansible YAML objects get past here, ruamel.yaml dumps will fail.
            if isinstance(value, str):
                value = str(value)
            commented_params[key] = value

        module_comment = ""
        module_comment_parts = target_task.ca.items.pop(module, [])
        comment: Optional[CommentToken]
        for comment in module_comment_parts:
            if not comment:
                continue
            module_comment += comment.value
        module_comment_stripped = module_comment.strip()

        if module_comment.endswith("\n\n"):
            # re-add a newline after the task block
            # https://stackoverflow.com/a/42199053
            ct = CommentToken("\n\n", CommentMark(0), None)
            last_key = list(action.keys())[-1]
            commented_params.ca.items[last_key] = [None, None, ct, None]

        if module_comment_stripped:
            # there's actually a comment, not just whitespace
            target_task.yaml_add_eol_comment(module_comment_stripped, module)

        target_task[module] = commented_params

        # call self._fixed(match) when data has been transformed to fix the error.
        self._fixed(match)
