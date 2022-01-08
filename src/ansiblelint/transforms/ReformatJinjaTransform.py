import os
from typing import Union

from ansible.template import Templar
from jinja2.environment import Environment
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.VariableHasSpacesRule import VariableHasSpacesRule
from ansiblelint.transforms import Transform
from ansiblelint.transform_utils import dump
from ansiblelint.utils import ansible_templar, nested_items_path


class ReformatJinjaTransform(Transform):
    id = "reformat-jinja"
    shortdesc = "Reformat Jinja2 expressions to add spaces."
    description = VariableHasSpacesRule.base_msg + (
        " {{ var_name }}. " "This re-formats expressions to add the spaces."
    )
    version_added = "5.3"

    wants = VariableHasSpacesRule
    tags = VariableHasSpacesRule.tags

    bracket_regex = VariableHasSpacesRule.bracket_regex
    exclude_json_re = VariableHasSpacesRule.exclude_json_re

    def __call__(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to fix the MatchError."""
        basedir: str = os.path.abspath(os.path.dirname(str(lintable.path)))
        templar: Templar = ansible_templar(basedir, templatevars={})
        jinja_env: Environment = templar.environment

        target_task: CommentedMap = self._seek(match.yaml_path, data)

        fixed = False
        for key, value, parent_path in nested_items_path(target_task):
            if not (isinstance(value, str) and templar.is_template(value)):
                continue
            # value is a jinja expression
            ast = jinja_env.parse(value)
            new_value = dump(node=ast, environment=jinja_env)
            if parent_path:
                target = self._seek(parent_path, target_task)
                target[key] = new_value
            else:
                target_task[key] = new_value
            fixed = True

        if fixed:
            self._fixed(match)
