from typing import Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.rules.UsingBareVariablesIsDeprecatedRule import UsingBareVariablesIsDeprecatedRule
from ansiblelint.transforms import Transform


class WrapBareVarsTransform(Transform):
    id = "wrap-bare-vars"
    shortdesc = "Wrap bare vars in {{ }} jinja blocks."
    description = (
        "Using bare variables is deprecated. This updates your "
        "playbooks by wrapping bare vars in jinja braces using"
        "this syntax: ``{{ your_variable }}``"
    )
    version_added = "5.3"

    wants = UsingBareVariablesIsDeprecatedRule
    tags = UsingBareVariablesIsDeprecatedRule.tags

    def __call__(
            self, match: MatchError, data: Union[CommentedMap, CommentedSeq]
    ) -> None:
        """Transform data to fix the MatchError."""
        # call self._fixed(match) when data has been transformed to fix the error.
        self._fixed(match)
