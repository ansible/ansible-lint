# Copyright (c) 2016, Tsukinowa Inc. <info@tsukinowa.jp>
# Copyright (c) 2018, Ansible Project
from typing import Any, Dict, List, MutableMapping, MutableSequence, Tuple, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.utils import (
    get_normalized_tasks_including_skipped,
    parse_yaml_linenumbers,
)


class TaskNoLocalAction(AnsibleLintRule, TransformMixin):
    id = 'deprecated-local-action'
    shortdesc = "Do not use 'local_action', use 'delegate_to: localhost'"
    description = 'Do not use ``local_action``, use ``delegate_to: localhost``'
    transform_description = (
        "Using ``local_action`` is deprecated. This updates your "
        "playbooks by replacing ``local_action`` tasks with:"
        "``delegate_to: localhost``"
    )
    severity = 'MEDIUM'
    tags = ['deprecations']
    version_added = 'v4.0.0'

    def match(self, line: str) -> Union[bool, str]:
        if 'local_action' in line:
            return True
        return False

    @staticmethod
    def _clean_task_and_params(
        task: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Union[MutableMapping[str, Any], str, None]]:
        # see ansiblelint.utils.normalize_task()
        action: Dict[str, Any] = task["action"].copy()
        # '__ansible_arguments__' includes _raw_params or argv
        arguments = action.pop("__ansible_arguments__")

        internal_keys = [k for k in action if k.startswith("__") and k.endswith("__")]
        for internal_key in internal_keys:
            del action[internal_key]

        params: Union[MutableMapping[str, Any], str, None] = None
        if arguments and isinstance(arguments, MutableMapping):
            # this can happen with set_fact and add_host modules
            action.update(arguments)
            params = action
        elif arguments and isinstance(arguments, MutableSequence):
            # a _raw_params module like command, shell, script, etc
            params = " ".join(arguments)
        elif arguments and isinstance(arguments, str):
            # str() to drop AnsibleUnicode
            params = str(arguments)
        elif action:
            params = action

        return action, params

    @staticmethod
    def _extract_comments(
        params: Union[MutableMapping[str, Any], str, None], target_task: CommentedMap
    ) -> Tuple[Union[CommentedMap, str, None], List[str]]:
        """Extract comments from the target_task.

        Comments will be attached to params where possible or returned in
        a list of comments to be used as eol comments.
        """
        local_action = target_task["local_action"]
        local_action_ca = getattr(local_action, "ca", None)
        local_action_module_comment = None
        if local_action_ca and "module" in local_action_ca.items:
            local_action_module_comment = local_action_ca.items["module"]

        # We can't just use the ansible-normalized values or
        # ruamel.yaml gets confused with AnsibleYAMLObjects
        if isinstance(params, MutableMapping):
            commented_params = CommentedMap()
            if local_action_ca:
                commented_params.ca.comment = local_action_ca.comment
                commented_params.ca.end = local_action_ca.end
                commented_params.ca.pre = local_action_ca.pre
            for key in params.keys():
                key = str(key)  # drop AnsibleUnicode
                commented_params[key] = local_action[key]
                if local_action_ca and key in local_action_ca.items:
                    commented_params.ca.items[key] = local_action_ca.items[key]
            params = commented_params

        comments = []
        for possible_comment in [
            target_task.ca.items.pop("local_action", None),
            local_action_module_comment,
        ]:
            if not possible_comment:
                continue
            # post_key, pre_key, post_value, pre_value
            for index, comment in enumerate(possible_comment):
                if not comment:
                    continue
                comments.append(comment.value)
        return params, comments

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq, str],
    ) -> None:
        """Transform data to replace the local_action."""
        # TaskNoLocalAction matches lines, not tasks.
        # So we need to resolve the ansible bits instead of grabbing match.task
        yaml = parse_yaml_linenumbers(lintable)
        tasks = get_normalized_tasks_including_skipped(yaml, lintable)

        normalized_task: Dict[str, Any] = self._seek(match.yaml_path, tasks)
        target_task: CommentedMap = self._seek(match.yaml_path, data)

        # semantics of which one is fqcn may change in future versions
        # module_normalized = normalized_task["action"]["__ansible_module__"]
        module = normalized_task["action"]["__ansible_module_original__"]

        # get order of the keys in the index
        position = list(target_task.keys()).index("local_action")

        action, params = self._clean_task_and_params(normalized_task)

        # This will replace params with a CommentedMap if needed.
        params, eol_comments = self._extract_comments(params, target_task)

        target_task.insert(position, module, params)

        # move any comments to the new location
        if eol_comments:
            # at least two spaces or the file indentation gets messed up
            target_task.yaml_add_eol_comment("  ".join(eol_comments), module)

        delegate_to = normalized_task.get("delegate_to", "localhost")
        target_task.insert(position, "delegate_to", delegate_to)

        del target_task["local_action"]

        fixed = True
        # call self._fixed(match) when data has been transformed to fix the error.
        if fixed:
            self._fixed(match)
