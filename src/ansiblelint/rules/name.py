"""Implementation of NameRule."""
import sys
from typing import TYPE_CHECKING, Any, Dict, Union

from ansiblelint.errors import MatchError
from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from typing import Optional

    from ansiblelint.file_utils import Lintable


class NameRule(AnsibleLintRule):
    """All tasks should be named."""

    id = "name"
    description = (
        "All tasks should have a distinct name for readability "
        "and for ``--start-at-task`` to work"
    )
    severity = "MEDIUM"
    tags = ["idiom"]
    version_added = "historic"

    def matchtask(
        self, task: Dict[str, Any], file: "Optional[Lintable]" = None
    ) -> Union[bool, str, MatchError]:
        if not task.get("name"):
            return self.create_matcherror(
                linenumber=task["__line__"], tag="name[missing]", filename=file
            )
        return False


if "pytest" in sys.modules:  # noqa: C901

    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import Runner

    def test_file_positive() -> None:
        """Positive test for unnamed-task."""
        collection = RulesCollection()
        collection.register(NameRule())
        success = "examples/playbooks/task-has-name-success.yml"
        good_runner = Runner(success, rules=collection)
        assert [] == good_runner.run()

    def test_file_negative() -> None:
        """Negative test for unnamed-task."""
        collection = RulesCollection()
        collection.register(NameRule())
        failure = "examples/playbooks/task-has-name-failure.yml"
        bad_runner = Runner(failure, rules=collection)
        errs = bad_runner.run()
        assert len(errs) == 4
