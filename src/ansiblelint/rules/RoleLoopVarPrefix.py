"""Optional Ansible-lint rule to enforce use of prefix on role loop vars."""
from typing import TYPE_CHECKING, List

from ansiblelint.config import options
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule
from ansiblelint.text import toidentifier

if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.constants import odict


class RoleLoopVarPrefix(AnsibleLintRule):
    """Role loop_var should use configured prefix."""

    id = 'no-loop-var-prefix'
    shortdesc = __doc__
    link = (
        "https://docs.ansible.com/ansible/latest/user_guide/"
        "playbooks_loops.html#defining-inner-and-outer-variable-names-with-loop-var"
    )
    description = """\
Looping inside roles has the risk of clashing with loops from user-playbooks.\
"""

    tags = ['idiom']
    prefix = ""
    severity = 'MEDIUM'

    def matchplay(self, file: Lintable, data: "odict[str, Any]") -> List[MatchError]:
        """Return matches found for a specific playbook."""
        results: List[MatchError] = []

        if not options.loop_var_prefix:
            return results
        self.prefix = options.loop_var_prefix.format(role=toidentifier(file.role))
        self.shortdesc = f"{self.__class__.shortdesc}: {self.prefix}"

        if file.kind not in ('tasks', 'handlers'):
            return results

        results.extend(self.handle_play(file, data))
        return results

    def handle_play(
        self, lintable: Lintable, task: "odict[str, Any]"
    ) -> List[MatchError]:
        """Return matches for a playlist."""
        results = []
        if 'block' in task:
            results.extend(self.handle_tasks(lintable, task['block']))
        else:
            results.extend(self.handle_task(lintable, task))
        return results

    def handle_tasks(
        self, lintable: Lintable, tasks: List["odict[str, Any]"]
    ) -> List[MatchError]:
        """Return matches for a list of tasks."""
        results = []
        for play in tasks:
            results.extend(self.handle_play(lintable, play))
        return results

    def handle_task(
        self, lintable: Lintable, task: "odict[str, Any]"
    ) -> List[MatchError]:
        """Return matches for a specific task."""
        results = []
        has_loop = 'loop' in task
        for key in task.keys():
            if key.startswith('with_'):
                has_loop = True

        if has_loop:
            loop_control = task.get('loop_control', {})
            loop_var = loop_control.get('loop_var', "")

            if not loop_var or not loop_var.startswith(self.prefix):
                results.append(
                    self.create_matcherror(
                        filename=lintable, linenumber=task['__line__']
                    )
                )
        return results
