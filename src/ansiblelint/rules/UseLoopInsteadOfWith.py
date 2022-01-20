import os
import sys
from typing import Any, Dict, List, Optional, Union, cast

from ansible.template import Templar
from jinja2 import nodes
from jinja2.environment import Environment
from jinja2.visitor import NodeTransformer
from ruamel.yaml import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.transform_utils import dump
from ansiblelint.utils import LINE_NUMBER_KEY, ansible_templar


# noinspection PyMethodMayBeStatic
class UseLoopInsteadOfWith(AnsibleLintRule, TransformMixin):
    id = "no-with-loops"
    shortdesc = "Use loop instead of with_* style loops."
    description = shortdesc + (
        " The ``with_*`` style loops make it difficult to use automated "
        "tooling, like schemas, to validate playbooks."
    )
    severity = "LOW"
    tags = ["deprecations", "opt-in", "experimental"]
    version_added = "5.3"

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        with_keys = [key for key in task if key.startswith("with_")]
        has_with_style_loop = bool(with_keys)
        return has_with_style_loop

    # NB: several lookups are in the community.general collection:
    #     flattened, cartesian
    #     So, transform() needs to handle this (common-ish) with_ loop,
    #     but, we can't run it through tests because we don't want to
    #     depend on collections.

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq, str],
    ) -> None:
        fixed = False
        target_task = self._seek(match.yaml_path, data)
        loop_type = next(key for key in match.task if key.startswith("with_"))

        basedir: str = os.path.abspath(os.path.dirname(str(lintable.path)))
        templar: Templar = ansible_templar(basedir, templatevars={})
        jinja_env: Environment = templar.environment

        with2loop = getattr(self, f"_replace_{loop_type}", None)
        if callable(with2loop):
            fixed = with2loop(loop_type, match.task, target_task, jinja_env)

        if fixed:
            self._fixed(match)

    def _set_loop_value(
        self, loop_type: str, loop_value: Any, target_task: CommentedMap
    ):
        position = list(target_task.keys()).index(loop_type)
        target_task.insert(position, "loop", loop_value)
        comment = target_task.ca.items.pop(loop_type, None)
        if comment is not None:
            target_task.ca.items["loop"] = comment
        del target_task[loop_type]

    # noinspection PyUnusedLocal
    def _replace_with_list(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        jinja_env: Environment,
    ) -> bool:
        with_list = target_task[loop_type]
        self._set_loop_value(loop_type, with_list, target_task)
        return True

    # noinspection PyUnusedLocal
    def _replace_with_items(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        jinja_env: Environment,
    ) -> bool:
        with_items = target_task[loop_type]
        vars_ = None
        if isinstance(with_items, list):
            vars_ = target_task.get("vars", CommentedMap())
            var_name = "items"
            while var_name in vars_:
                var_name += "_"
            vars_[var_name] = with_items

            loop_value = "{{" + var_name + "}}"
        else:
            loop_value = with_items

        ast = jinja_env.parse(loop_value)
        output_node = cast(nodes.Output, ast.body[0])
        if len(output_node.nodes) != 1:
            # unexpected template.
            # There shouldn't be TemplateData nodes or more than one expression.
            return False
        node: nodes.Node = output_node.nodes[0]
        output_node.nodes[0] = nodes.Filter(
            node, "flatten", [], [nodes.Keyword("levels", nodes.Const(1))], None, None
        )
        loop_value = cast(str, dump(node=ast, environment=jinja_env))

        if vars_ is not None:
            comment = target_task.ca.items.pop("vars", None)
            target_task["vars"] = vars_
            if comment is not None:
                target_task.ca.items["vars"] = comment

        self._set_loop_value(loop_type, loop_value, target_task)
        return True


if 'pytest' in sys.modules:

    import pytest

    from ansiblelint.testing import RunFromText  # pylint: disable=ungrouped-imports

    LOOP = '''
- hosts: all
  tasks:
    - name: Pass when loop is used
      debug:
        msg: "{{ item }}"
      loop:
        - hello
        - world
'''

    WITH_ITEMS = '''
- hosts: all
  tasks:
    - name: Fail when with_items is used
      debug:
        msg: "{{ item }}"
      with_items:
        - hello
        - world
'''

    WITH_INDEXED_ITEMS = '''
- hosts: all
  tasks:
    - name: Fail when with_indexed_items is used
      debug:
        msg: "{{ item.0 }} - {{ item.1 }}"
      with_indexed_items: "{{ items }}"
'''

    @pytest.mark.parametrize(
        'rule_runner', (UseLoopInsteadOfWith,), indirect=['rule_runner']
    )
    def test_loop(rule_runner: RunFromText) -> None:
        """The task uses 'loop' to loop."""
        results = rule_runner.run_playbook(LOOP)
        assert len(results) == 0

    @pytest.mark.parametrize(
        'rule_runner', (UseLoopInsteadOfWith,), indirect=['rule_runner']
    )
    def test_no_with_items(rule_runner: RunFromText) -> None:
        """The task uses 'with_items' to loop."""
        results = rule_runner.run_playbook(WITH_ITEMS)
        assert len(results) == 1

    @pytest.mark.parametrize(
        'rule_runner', (UseLoopInsteadOfWith,), indirect=['rule_runner']
    )
    def test_no_with_indexed_items(rule_runner: RunFromText) -> None:
        """The task uses 'with_indexed_items' to loop."""
        results = rule_runner.run_playbook(WITH_INDEXED_ITEMS)
        assert len(results) == 1
