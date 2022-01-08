from typing import Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.TaskHasNameRule import TaskHasNameRule
from ansiblelint.transforms import Transform


class StubTaskNameTransform(Transform):
    id = "stub-task-name"
    shortdesc = "Add task name stubs to simplify naming all tasks."
    description = (
        "All tasks should have a distinct name for readability "
        "and for ``--start-at-task`` to work. This adds an empty "
        "name to every unnamed task to simplify adding names to "
        "tasks."
    )
    version_added = "5.3"

    wants = TaskHasNameRule
    tags = TaskHasNameRule.tags

    # comment to add on the stubbed name: lines
    comment = "TODO: Name this task"

    def __call__(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to simplify manually fixing the MatchError."""
        # This transform does not fully fix errors.
        # Do not call self._fixed(match).
        target_task: CommentedMap = self._seek(match.yaml_path, data)
        target_task.insert(0, "name", None, self.comment)
