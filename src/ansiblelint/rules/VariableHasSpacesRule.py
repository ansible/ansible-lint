# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018, Ansible Project

import os
import re
import sys
from typing import Any, Dict, List, Optional, Union

from ansible.template import Templar
from jinja2.environment import Environment
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.transform_utils import dump
from ansiblelint.utils import ansible_templar, nested_items, nested_items_path


class VariableHasSpacesRule(AnsibleLintRule, TransformMixin):
    id = 'var-spacing'
    base_msg = 'Variables should have spaces before and after: '
    shortdesc = base_msg + ' {{ var_name }}'
    description = 'Variables should have spaces before and after: ``{{ var_name }}``'
    severity = 'LOW'
    tags = ['formatting']
    version_added = 'v4.0.0'

    bracket_regex = re.compile(r"{{[^{\n' -]|[^ '\n}-]}}", re.MULTILINE | re.DOTALL)
    exclude_json_re = re.compile(r"[^{]{'\w+': ?[^{]{.*?}}", re.MULTILINE | re.DOTALL)

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        for k, v, _ in nested_items(task):
            if isinstance(v, str):
                cleaned = self.exclude_json_re.sub("", v)
                if bool(self.bracket_regex.search(cleaned)):
                    return self.base_msg + v
        return False

    def transform(
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


if 'pytest' in sys.modules:

    import pytest

    from ansiblelint.rules import RulesCollection  # pylint: disable=ungrouped-imports
    from ansiblelint.runner import Runner  # pylint: disable=ungrouped-imports

    @pytest.fixture
    def error_expected_lines() -> List[int]:
        """Return list of expected error lines."""
        return [23, 26, 29, 54, 65]

    @pytest.fixture
    def test_playbook() -> str:
        """Return test cases playbook path."""
        return "examples/playbooks/var-spacing.yml"

    @pytest.fixture
    def lint_error_lines(test_playbook: str) -> List[int]:
        """Get VarHasSpacesRules linting results on test_playbook."""
        collection = RulesCollection()
        collection.register(VariableHasSpacesRule())
        lintable = Lintable(test_playbook)
        results = Runner(lintable, rules=collection).run()
        return list(map(lambda item: item.linenumber, results))

    def test_var_spacing(
        error_expected_lines: List[int], lint_error_lines: List[int]
    ) -> None:
        """Ensure that expected error lines are matching found linting error lines."""
        # list unexpected error lines or non-matching error lines
        error_lines_difference = list(
            set(error_expected_lines).symmetric_difference(set(lint_error_lines))
        )
        assert len(error_lines_difference) == 0
