"""All internal ansible-lint transforms."""
import logging
from typing import (
    Any,
    List,
    MutableSequence,
    MutableMapping,
    Type,
    Union,
)

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from .._internal.rules import BaseRule
from ..errors import MatchError
from ..file_utils import Lintable

_logger = logging.getLogger(__name__)


# loosely based on AnsibleLintRule
class Transform:
    """Root class used by Transforms."""

    id: str = ""
    tags: List[str] = []
    shortdesc: str = ""
    description: str = ""
    version_added: str = ""
    link: str = ""

    """wants is the class that this Transform handles"""
    wants: Type[BaseRule]

    @staticmethod
    def _fixed(match: MatchError) -> None:
        """Mark a match as fixed (transform was successful, so issue should be resolved)."""
        match.fixed = True

    def __call__(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq, str],
    ) -> None:
        """Transform data to fix the MatchError."""
        # call self._fixed(match) when data has been transformed to fix the error.

    @staticmethod
    def _seek(
        yaml_path: List[Union[int, str]], data: Union[MutableMapping, MutableSequence]
    ) -> Any:
        target = data
        for segment in yaml_path:
            target = target[segment]
        return target

    def verbose(self) -> str:
        """Return a verbose representation of the transform."""
        return self.id + ": " + self.shortdesc + "\n  " + self.description

    def __lt__(self, other: "Transform") -> bool:
        """Enable us to sort transforms by their id."""
        return self.id < other.id
