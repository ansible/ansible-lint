from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.utils import LINE_NUMBER_KEY, convert_to_boolean

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    # pylint: disable=ungrouped-imports
    from ansiblelint.constants import odict
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class NoFormattingInWhenRule(AnsibleLintRule, TransformMixin):
    id = 'no-jinja-when'
    shortdesc = 'No Jinja2 in when'
    description = (
        '``when`` is a raw Jinja2 expression, remove redundant {{ }} from variable(s).'
    )
    severity = 'HIGH'
    tags = ['deprecations']
    version_added = 'historic'

    @staticmethod
    def _is_valid(when: str) -> bool:
        if not isinstance(when, str):
            return True
        return when.find('{{') == -1 and when.find('}}') == -1

    def matchplay(
        self, file: "Lintable", data: "odict[str, Any]"
    ) -> List["MatchError"]:
        errors: List["MatchError"] = []
        if isinstance(data, dict):
            if 'roles' not in data or data['roles'] is None:
                return errors
            for role in data['roles']:
                if self.matchtask(role, file=file):
                    errors.append(
                        self.create_matcherror(
                            details=str({'when': role}),
                            filename=file,
                            linenumber=role[LINE_NUMBER_KEY],
                        )
                    )
        if isinstance(data, list):
            for play_item in data:
                sub_errors = self.matchplay(file, play_item)
                if sub_errors:
                    errors = errors + sub_errors
        return errors

    def matchtask(
        self, task: Dict[str, Any], file: 'Optional[Lintable]' = None
    ) -> Union[bool, str]:
        return 'when' in task and not self._is_valid(task['when'])

    def transform(
        self,
        match: "MatchError",
        lintable: "Lintable",
        data: "Union[CommentedMap, CommentedSeq, str]",
    ) -> None:
        """Transform data to fix the MatchError."""
        fixed = False

        # target is the role or a task with the wrapped when expression
        target: Optional[Dict[str, Any]] = None

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
