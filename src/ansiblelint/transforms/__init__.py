"""All internal ansible-lint transforms."""
import glob
import importlib.util
import logging
import os
from argparse import Namespace
from importlib.abc import Loader
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    MutableSequence,
    MutableMapping,
    Optional,
    Type,
    Union,
)

from ruamel.yaml.comments import CommentedMap, CommentedSeq

import ansiblelint.file_utils
import ansiblelint.utils

from .._internal.rules import BaseRule
from ..config import options as ansiblelint_options
from ..errors import MatchError
from ..file_utils import Lintable

__all__ = ["Transform", "TransformsCollection"]

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
        data: Union[CommentedMap, CommentedSeq],
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

    @staticmethod
    def _get_ansible_tasks(lintable: Lintable):
        yaml = ansiblelint.utils.parse_yaml_linenumbers(lintable)
        # we can't use ansiblelint.utils.get_normalized_tasks
        # because it does not normalize tasks tagged with skip_ansible_lint
        raw_tasks = ansiblelint.utils.get_action_tasks(yaml, lintable)
        tasks = []
        for raw_task in raw_tasks:
            try:
                tasks.append(
                    ansiblelint.utils.normalize_task(raw_task, str(lintable.path))
                )
            except MatchError as e:
                # This gets raised from AnsibleParserError.
                # Leave it as-is to keep the task indexes the same.
                raw_task["__match_error__"] = e
                tasks.append(raw_task)
        return tasks


# TODO: is_valid_transform and load_plugins are essentially the same as is_valid_rule and load_plugins
#       refactor so both rules and transforms can use the same functions


def is_valid_transform(transform: Transform) -> bool:
    """Check if given transform is valid or not."""
    return (
        isinstance(transform, Transform)
        and bool(transform.id)
        and bool(transform.shortdesc)
        and getattr(transform, "wants", None) is not None
    )


def load_plugins(directory: str) -> Iterator[Transform]:
    """Yield a transform class."""
    for pluginfile in glob.glob(os.path.join(directory, '[A-Za-z]*.py')):

        pluginname = os.path.basename(pluginfile.replace('.py', ''))
        spec = importlib.util.spec_from_file_location(pluginname, pluginfile)
        # https://github.com/python/typeshed/issues/2793
        if spec and isinstance(spec.loader, Loader):
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                transform = getattr(module, pluginname)()
                if is_valid_transform(transform):
                    yield transform

            except (TypeError, ValueError, AttributeError):
                _logger.warning("Skipped invalid transform from %s", pluginname)


class TransformsCollection:
    """A container to load and register and retrieve transforms."""

    def __init__(
        self,
        transformsdirs: Optional[List[str]] = None,
        options: Namespace = ansiblelint_options,
    ) -> None:
        """Initialize a RulesCollection instance."""
        self.options = options
        if transformsdirs is None:
            transformsdirs = []
        self.transformsdirs = ansiblelint.file_utils.expand_paths_vars(transformsdirs)
        self.transforms: List[Transform] = []
        for transformsdir in self.transformsdirs:
            _logger.debug("Loading transforms from %s", transformsdir)
            for transform in load_plugins(transformsdir):
                self.register(transform)
        self.transforms = sorted(self.transforms)

        # key is rule's id (rule class loading prevents keying on class)
        self.transforms_by_rule: Dict[str, List[Transform]] = {}
        for transform in self.transforms:
            rule = transform.wants.id
            if rule not in self.transforms_by_rule:
                self.transforms_by_rule[rule] = []
            self.transforms_by_rule[rule].append(transform)

    def register(self, obj: Transform) -> None:
        """Register a new transform."""
        # We skip opt-in transforms which were not manually enabled
        if (
            'opt-in' not in obj.tags or obj.id in self.options.enable_list
        ):  # TODO: adjust for transforms
            self.transforms.append(obj)

    def __iter__(self) -> Iterator[Transform]:
        """Return the iterator over the transforms in the RulesCollection."""
        return iter(self.transforms)

    def __len__(self) -> int:
        """Return the length of the RulesCollection data."""
        return len(self.transforms)

    def extend(self, more: List[Transform]) -> None:
        """Register multiple new transforms."""
        self.transforms.extend(more)

    def __repr__(self) -> str:
        """Return a RulesCollection instance representation."""
        return "\n".join(
            [
                transform.verbose()
                for transform in sorted(self.transforms, key=lambda x: x.id)
            ]
        )

    def get_transforms_for(self, match: MatchError) -> List[Transform]:
        """Lookup any relevant transforms to resolve a MatchError."""
        transforms = self.transforms_by_rule.get(match.rule.id, [])
        return transforms
