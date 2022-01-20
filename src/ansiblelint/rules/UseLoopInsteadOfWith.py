import functools
import os
import sys
from typing import Any, Dict, List, MutableMapping, Optional, Union, cast

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


def filter_with_flatten(
    jinja_env: Environment, loop_value: str, levels: int = None
) -> Optional[str]:
    loop_ast = jinja_env.parse(loop_value)
    output_node = cast(nodes.Output, loop_ast.body[0])
    if len(output_node.nodes) != 1:
        # unexpected template.
        # There shouldn't be TemplateData nodes or more than one expression.
        return None
    node: nodes.Node = output_node.nodes[0]
    kwargs = []
    if levels is not None:
        kwargs.append(nodes.Keyword("levels", nodes.Const(1)))
    output_node.nodes[0] = nodes.Filter(node, "flatten", [], kwargs, None, None)
    return dump(node=loop_ast, environment=jinja_env)


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

    @staticmethod
    def _set_loop_value(loop_type: str, loop_value: Any, target_task: CommentedMap):
        position = list(target_task.keys()).index(loop_type)
        target_task.insert(position, "loop", loop_value)
        comment = target_task.ca.items.pop(loop_type, None)
        if comment is not None:
            target_task.ca.items["loop"] = comment
        del target_task[loop_type]

    @staticmethod
    def _set_vars(vars_: Optional[CommentedMap], target_task: CommentedMap):
        if vars_ is None:
            return
        comment = target_task.ca.items.pop("vars", None)
        target_task["vars"] = vars_
        if comment is not None:
            target_task.ca.items["vars"] = comment

    @staticmethod
    def _unique_vars_name(vars_: Optional[CommentedMap], var_name: str):
        while vars_ and var_name in vars_:
            var_name += "_"
        return var_name

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
        flatten_levels: Optional[int] = 1,
    ) -> bool:
        with_items = target_task[loop_type]
        vars_ = None
        if isinstance(with_items, list):
            vars_ = target_task.get("vars", CommentedMap())
            var_name = self._unique_vars_name(vars_, "items")
            vars_[var_name] = with_items

            loop_value = "{{" + var_name + "}}"
        else:
            loop_value = with_items

        loop_value = filter_with_flatten(jinja_env, loop_value, levels=flatten_levels)
        if loop_value is None:
            # unexpected template.
            # There shouldn't be TemplateData nodes or more than one expression.
            return False

        self._set_vars(vars_, target_task)
        self._set_loop_value(loop_type, loop_value, target_task)
        return True

    # flattend lookup is in the community.general collection (see note above)
    _replace_with_flattened = functools.partialmethod(
        _replace_with_items, flatten_levels=None
    )

    def _replace_with_indexed_items(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        jinja_env: Environment,
    ) -> bool:
        with_indexed_items = target_task[loop_type]
        vars_ = target_task.get("vars", None)
        if isinstance(with_indexed_items, list):
            if vars_ is None:
                vars_ = CommentedMap()
            var_name = self._unique_vars_name(vars_, "items")
            vars_[var_name] = with_indexed_items

            loop_value = "{{" + var_name + "}}"
        else:
            loop_value = with_indexed_items

        index_var_name = self._unique_vars_name(vars_, "index")

        loop_value = filter_with_flatten(jinja_env, loop_value, levels=1)
        if loop_value is None:
            # unexpected template.
            # There shouldn't be TemplateData nodes or more than one expression.
            return False

        position = list(target_task.keys()).index(loop_type)

        self._set_vars(vars_, target_task)
        self._set_loop_value(loop_type, loop_value, target_task)

        if "loop_control" not in target_task:
            target_task.insert(position + 1, "loop_control", CommentedMap())
        elif not isinstance(target_task["loop_control"], MutableMapping):
            target_task["loop_control"] = CommentedMap()
        target_task["loop_control"]["index_var"] = index_var_name
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
