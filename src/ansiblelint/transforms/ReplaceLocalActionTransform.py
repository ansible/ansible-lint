from typing import MutableMapping, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.TaskNoLocalAction import TaskNoLocalAction
from ansiblelint.transforms import Transform


class ReplaceLocalActionTransform(Transform):
    id = "replace-local-action"
    shortdesc = "Replace 'local_action' with 'delegate_to: localhost'."
    description = (
        "Using ``local_action`` is deprecated. This updates your "
        "playbooks by replacing ``local_action`` tasks with:"
        "``delegate_to: localhost``"
    )
    version_added = "5.3"

    wants = TaskNoLocalAction
    tags = TaskNoLocalAction.tags

    def __call__(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to replace the local_action."""

        # TaskNoLocalAction matches lines, not tasks.
        # So we need to resolve the ansible bits instead of grabbing match.task
        tasks = self._get_ansible_tasks(lintable)

        normalized_task: dict = self._seek(match.yaml_path, tasks)
        target_task: CommentedMap = self._seek(match.yaml_path, data)

        # see ansiblelint.utils.normalize_task()
        # semantics of which one is fqcn may change in future versions
        action: dict = normalized_task["action"].copy()
        # module_normalized = action.pop("__ansible_module__")
        module = action.pop("__ansible_module_original__")
        # '__ansible_arguments__' includes _raw_params or argv
        arguments = action.pop("__ansible_arguments__")

        internal_keys = [k for k in action if k.startswith("__") and k.endswith("__")]
        for internal_key in internal_keys:
            del action[internal_key]

        # get order of the keys in the index
        position = list(target_task.keys()).index("local_action")

        params = None
        # TODO: would I ever need both args and params?
        if arguments:
            params = " ".join(arguments)
        elif action:
            params = action

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

        target_task.insert(position, module, params)

        # move any comments to the new location
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
        if comments:
            # at least two spaces or the file indentation gets messed up
            target_task.yaml_add_eol_comment("  ".join(comments), module)

        delegate_to = normalized_task.get("delegate_to", "localhost")
        target_task.insert(position, "delegate_to", delegate_to)

        del target_task["local_action"]

        fixed = True
        # call self._fixed(match) when data has been transformed to fix the error.
        if fixed:
            self._fixed(match)
