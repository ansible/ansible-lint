"""Rule that flags action shorthand."""
import sys
from typing import Any, Dict, Optional, Union

from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule


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


class TaskNoActionShorthand(AnsibleLintRule):

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
