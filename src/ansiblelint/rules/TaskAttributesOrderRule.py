"""Optional rule to enforce task attributes order."""
import logging
import sys
# from collections import OrderedDict as odict
from ansiblelint.constants import odict
from pprint import pp, pprint
from typing import TYPE_CHECKING, Any, Dict, Union, List

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Any

    from ansiblelint.file_utils import Lintable
    from ansiblelint.errors import MatchError
    from ansiblelint.constants import odict


# _logger = logging.getLogger(__name__)
logging.basicConfig(filename='example.log', level=logging.DEBUG)


class TaskAttributesOrderRule(AnsibleLintRule):
    """Enforce task attribute order."""

    id = 'attribute-order'
    shortdesc = __doc__
    description = 'Task attributes should be in the same order across all lintables'
    severity = 'LOW'
    tags = ['opt-in', 'formatting', 'experimental']
    version_added = 'v5.2.2'

    # skipped rules causes error
    # delegate_to is always present
    # tags is never in the right order
    removed_attributes = ['skipped_rules', 'delegate_to', 'tags']
    possible_attrs = [
        "name",
        "any_errors_fatal",
        "async",
        "become",
        "become_exe",
        "become_flags",
        "become_method",
        "become_user",
        "changed_when",
        "check_mode",
        "collections",
        "connection",
        "debugger",
        "delay",
        "delegate_facts",
        "delegate_to",
        "diff",
        "environment",
        "failed_when",
        "ignore_errors",
        "ignore_unreachable",
        "local_action",
        "module_defaults",
        "no_log",
        "poll",
        "port",
        "register",
        "remote_user",
        "retries",
        "run_once",
        "throttle",
        "timeout",
        "until",
        "vars",
        "when",
        "action",
        "args",
        "notify",
        "loop",
        "loop_control",
        "tags",
        # "with_",
    ]
    ordered_expected_attrs = odict((key, idx) for idx, key in enumerate(possible_attrs))


    def matchplay(self, file: Lintable, data: "odict[str, Any]") -> List[MatchError]:
        """Return matches found for a specific playbook."""
        results: List[MatchError] = []

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

        pprint(task['name'])
        logging.info(task['name'])

        attrs = []
        for k in task.keys():
            if not k.startswith('__') and (k not in self.removed_attributes):
                attrs.append(k)

        # loop through actual attrs and look up their position in the expected order
        actual_attrs = odict()
        for attr in attrs:
            actual_attrs[attr] = self.ordered_expected_attrs[attr]

        sorted_actual_attrs = odict(
            sorted(actual_attrs.items(), key=lambda item: item[1])
        )

        logging.info((task.get('name'), actual_attrs))
        # logging.info(('sorted:', sorted_actual_attrs))
        # logging.info(sorted_actual_attrs != actual_attrs)

        if sorted_actual_attrs != actual_attrs:
            return "Please verify the order of the attributes in this task."

        return results
