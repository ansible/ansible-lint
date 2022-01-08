from typing import Optional, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.NoFormattingInWhenRule import (
    NoFormattingInWhenRule,
)
from ansiblelint.transforms import Transform
from ansiblelint.utils import convert_to_boolean


class UnwrapJinjaWhenExpressionsTransform(Transform):
    id = "unwrap-jinja-when"
    shortdesc = "Unwrap 'when' Jinja2 expressions (remove {{ }})"
    description = (
        "``when`` is a raw Jinja2 expression. This updates your "
        "playbooks by removing the redundant {{ }} from variable(s)."
    )
    version_added = "5.3"

    wants = NoFormattingInWhenRule
    tags = NoFormattingInWhenRule.tags
    # noinspection PyProtectedMember
    _is_valid = NoFormattingInWhenRule._is_valid

    def __call__(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to fix the MatchError."""
        fixed = False

        # target is the role or a task with the wrapped when expression
        target: Optional[dict] = None

        if match.match_type == "play":
            # a role
            target_play = self._seek(match.yaml_path, data)
            for role in target_play.get("roles", []):
                # noinspection PyProtectedMember
                if "when" in role and not self._is_valid(role["when"]):
                    target = role
                    break
        else:
            # a task
            target = self._seek(match.yaml_path, data)

        if target:
            when_original = target["when"]
            when = self._unwrap(when_original)
            target["when"] = when
            fixed = True

        # call self._fixed(match) when data has been transformed to fix the error.
        if fixed:
            self._fixed(match)

    @staticmethod
    def _unwrap(when: str) -> Union[str, bool]:
        start = when.find("{{") + 2
        end = when.rfind("}}")
        expression = when[start:end].strip()
        try:
            return convert_to_boolean(expression)
        except TypeError:
            return expression
