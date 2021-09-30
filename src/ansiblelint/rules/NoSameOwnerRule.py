"""Optional rule for avoiding keeping owner/group when transferring files."""
import re
import sys
from typing import Any, List

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule


class NoSameOwnerRule(AnsibleLintRule):

    id = 'no-same-owner'
    shortdesc = 'Owner should not be kept between different hosts'
    description = """
Optional rule that highlights dangers of assuming that user/group on the remote
machines may not exist on ansible controller or vice versa. Owner and group
should not be preserved when transferring files between them.

This rule is not enabled by default and was inspired by Zuul execution policy.
See:
https://zuul-ci.org/docs/zuul-jobs/policy.html\
#preservation-of-owner-between-executor-and-remote
"""
    severity = 'LOW'
    tags = ['opt-in']

    def matchplay(self, file: Lintable, data: Any) -> List[MatchError]:
        """Return matches found for a specific playbook."""
        results: List[MatchError] = []
        if file.kind not in ('tasks', 'handlers', 'playbook'):
            return results

        results.extend(self.handle_play(file, data))
        return results

    def handle_play(self, lintable: Lintable, task: Any) -> List[MatchError]:
        """Process a play."""
        results = []
        if 'block' in task:
            results.extend(self.handle_playlist(lintable, task['block']))
        else:
            results.extend(self.handle_task(lintable, task))
        return results

    def handle_playlist(self, lintable: Lintable, playlist: Any) -> List[MatchError]:
        """Process a playlist."""
        results = []
        for play in playlist:
            results.extend(self.handle_play(lintable, play))
        return results

    def handle_task(self, lintable: Lintable, task: Any) -> List[MatchError]:
        """Process a task."""
        results = []
        if 'synchronize' in task:
            if self.handle_synchronize(task):
                print(task)
                results.append(
                    self.create_matcherror(
                        filename=lintable, linenumber=task['__line__']
                    )
                )
        elif 'unarchive' in task:
            if self.handle_unarchive(task):
                results.append(
                    self.create_matcherror(
                        filename=lintable, linenumber=task['__line__']
                    )
                )

        return results

    @staticmethod
    def handle_synchronize(task: Any) -> bool:
        """Process a synchronize task."""
        if task.get('delegate_to') is not None:
            return False

        synchronize = task['synchronize']
        archive = synchronize.get('archive', True)

        if synchronize.get('owner', archive) or synchronize.get('group', archive):
            return True
        return False

    @staticmethod
    def handle_unarchive(task: Any) -> bool:
        """Process unarchive task."""
        unarchive = task['unarchive']
        delegate_to = task.get('delegate_to')

        if (
            delegate_to == 'localhost'
            or delegate_to != 'localhost'
            and 'remote_src' not in unarchive
        ):
            if unarchive['src'].endswith('zip'):
                if '-X' in unarchive.get('extra_opts', []):
                    return True
            if re.search(r'.*\.tar(\.(gz|bz2|xz))?$', unarchive['src']):
                if '--no-same-owner' not in unarchive.get('extra_opts', []):
                    return True
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
                'examples/roles/role_for_no_same_owner/tasks/fail.yml', 10, id='fail'
            ),
            pytest.param(
                'examples/roles/role_for_no_same_owner/tasks/pass.yml', 0, id='pass'
            ),
        ),
    )
    def test_no_same_owner_rule(
        default_rules_collection: RulesCollection, test_file: str, failures: int
    ) -> None:
        """Test rule matches."""
        results = Runner(test_file, rules=default_rules_collection).run()
        assert len(results) == failures
        for result in results:
            assert result.message == NoSameOwnerRule.shortdesc
