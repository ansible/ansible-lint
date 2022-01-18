"""Rule that flags action shorthand."""
import sys
from typing import Any, Dict, MutableMapping, Optional, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import CommentMark
from ruamel.yaml.tokens import CommentToken

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin

FREE_FORM_MODULES = {
    "command",
    "shell",
    "script",
    "raw",
    "meta",
    "win_command",
    "win_shell",
    "include",
    "import_playbook",
    "import_tasks",
    "include_tasks",
    "include_vars",
}
FREE_FORM_MODULES = {
    m
    for mod in FREE_FORM_MODULES
    for m in (mod, f"ansible.builtin.{mod}", f"ansible.legacy.{mod}")
} | {
    "ansible.windows.win_command",
    "ansible.windows.win_shell",
}
# set_fact and add_host use _raw_params for a dict of vars. They are not free-form.


class TaskNoActionShorthand(AnsibleLintRule, TransformMixin):

    id = "no-action-shorthand"
    shortdesc = "Use YAML args instead of action shorthand."
    description = (
        "Use YAML args instead of action shorthand.\n"
        "Instead of ``module: arg1=value arg2=42``, use:\n"
        "  module:\n"
        "    arg1: value\n"
        "    arg2: 42\n"
        "Early versions of Ansible used a shorthand to define args, but "
        "(1) action shorthand relies on Ansible's magic type casting "
        "which is the source of many obscure, difficult-to-debug issues; and "
        "(2) schema based linting cannot detect issues when args are hidden "
        "in the action shorthand. "
    )
    # Action shorthand was removed from ansible's documentation after v2.9
    # https://docs.ansible.com/ansible/2.9/user_guide/playbooks_intro.html#action-shorthand
    severity = 'MEDIUM'
    tags = ['idiom']
    version_added = "5.3"

    needs_raw_task = True

    def matchrawtask(
        self,
        raw_task: Dict[str, Any],
        task: Dict[str, Any],
        file: Optional[Lintable] = None,
    ) -> Union[bool, str]:
        if task["action"]["__ansible_module__"] in FREE_FORM_MODULES:
            return False

        module = task["action"]["__ansible_module_original__"]
        raw_action_block = raw_task[module]
        if isinstance(raw_action_block, str):
            return True
        # raw_action_block should be a dict, which is what we want.
        # if isinstance(raw_action_block, dict):
        #     return False

        return False

    def _clean_task(self, task: dict) -> Optional[dict]:
        # see ansiblelint.utils.normalize_task()
        # semantics of which one is fqcn may change in future versions
        action: dict = task["action"].copy()
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

        return action

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to replace the action shorthand."""
        target_task: CommentedMap = self._seek(match.yaml_path, data)

        action = self._clean_task(match.task)
        module = match.task["action"]["__ansible_module_original__"]

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


# testing code to be loaded only with pytest or when executed the rule file
if "pytest" in sys.modules:

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.mark.parametrize(
        ("test_file", "failures"),
        (
            pytest.param(
                'examples/roles/role_for_no_action_shorthand/tasks/fail.yml',
                3,
                id='fail',
            ),
            pytest.param(
                'examples/roles/role_for_no_action_shorthand/tasks/pass.yml',
                0,
                id='pass',
            ),
        ),
    )
    def test_no_action_shorthand_rule(
        default_rules_collection: RulesCollection, test_file: str, failures: int
    ) -> None:
        """Test rule matches."""
        results = Runner(test_file, rules=default_rules_collection).run()
        assert len(results) == failures
        for result in results:
            assert result.message == TaskNoActionShorthand.shortdesc
