import functools
import os
import sys
from typing import (
    Any,
    Dict,
    MutableMapping,
    MutableSequence,
    Optional,
    Tuple,
    Union,
    cast,
)

from ansible.template import Templar
from jinja2 import nodes
from jinja2.environment import Environment
from jinja2.visitor import NodeTransformer
from ruamel.yaml import CommentedMap, CommentedSeq
from ruamel.yaml.error import CommentMark
from ruamel.yaml.tokens import CommentToken

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.transform_utils import dump
from ansiblelint.utils import ansible_templar, nested_items_path


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

        with2loop = getattr(self, f"_replace_{loop_type}", None)
        if callable(with2loop):
            fixed = with2loop(loop_type, match.task, target_task, templar)

        if fixed:
            self._fixed(match)

    # ### transform utility methods ###

    def _extract_comment(
        self, key: Union[str, int], target_task: CommentedMap
    ) -> Tuple[str, bool]:
        def get_comment(
            key_or_index: Union[str, int], target: Union[CommentedMap, CommentedSeq]
        ):
            item_comment = ""
            comment: Optional[CommentToken]
            for comment in target.ca.items.pop(key_or_index, []):
                if not comment:
                    continue
                item_comment += comment.value
            return item_comment

        key_comment = get_comment(key, target_task)

        last_key = list(target_task.keys())[-1]

        if key in target_task and isinstance(
            target_task[key], (MutableMapping, MutableSequence)
        ):
            for k, v, p in nested_items_path(target_task[key]):
                parent = self._seek(p, target_task[key])
                if hasattr(parent, "ca"):
                    key_comment += get_comment(k, parent)

        last_key_needs_newline = last_key == key and key_comment.endswith("\n\n")

        return key_comment.strip(), last_key_needs_newline

    def _set_loop_value(
        self, loop_type: str, loop_value: Any, target_task: CommentedMap
    ) -> bool:
        position = list(target_task.keys()).index(loop_type)
        target_task.insert(position, "loop", loop_value)
        comment, last_key_needs_newline = self._extract_comment(loop_type, target_task)
        if comment:
            target_task.yaml_add_eol_comment(comment, "loop")
        del target_task[loop_type]
        # Delay adding the last_key_comment_item as other keys might get added.
        return last_key_needs_newline

    def _set_vars(
        self, vars_: Optional[CommentedMap], target_task: CommentedMap
    ) -> bool:
        if vars_ is None:
            return False
        comment, last_key_needs_newline = self._extract_comment("vars", target_task)
        target_task["vars"] = vars_
        if comment:
            target_task.yaml_add_eol_comment(comment, "vars")
        # Delay adding the last_key_comment_item as other keys might get added.
        return last_key_needs_newline

    def _handle_last_key_newline(
        self, last_key_needs_newline: bool, target: Union[CommentedMap, CommentedSeq]
    ) -> None:
        if not last_key_needs_newline:
            return
        if isinstance(target, CommentedMap):
            last_key = list(target.keys())[-1]
        else:
            # the key here must be an actual index
            last_key = len(target) - 1

        if target[last_key] and isinstance(
            target[last_key], (CommentedMap, CommentedSeq)
        ):
            self._handle_last_key_newline(last_key_needs_newline, target[last_key])
            return

        if last_key in target.ca.items:
            last_key_comment_item = target.ca.items[last_key]
            if isinstance(target, CommentedMap):
                ct: CommentToken = last_key_comment_item[2]
            else:
                ct = last_key_comment_item[0]
            if not ct.value.endswith("\n\n"):
                ct.value = ct.value.strip() + "\n\n"
            return
        # re-add a newline after the task block
        # https://stackoverflow.com/a/42199053
        ct = CommentToken("\n\n", CommentMark(0), None)
        if isinstance(target, CommentedMap):
            last_key_comment_item = [None, None, ct, None]
        else:
            last_key_comment_item = [ct, None]
        target.ca.items[last_key] = last_key_comment_item

    @staticmethod
    def _unique_vars_name(vars_: Optional[CommentedMap], var_name: str):
        while vars_ and var_name in vars_:
            var_name += "_"
        return var_name

    # ### transform methods for each with_* variant ###

    # noinspection PyUnusedLocal
    def _replace_with_list(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        templar: Templar,
    ) -> bool:
        with_list = target_task[loop_type]
        needs_newline = self._set_loop_value(loop_type, with_list, target_task)
        self._handle_last_key_newline(needs_newline, target_task)
        return True

    # noinspection PyUnusedLocal
    def _replace_with_items(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        templar: Templar,
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

        loop_value = filter_with_flatten(
            templar.environment, loop_value, levels=flatten_levels
        )
        if loop_value is None:
            # unexpected template.
            # There shouldn't be TemplateData nodes or more than one expression.
            return False

        loop_had_newline = self._set_loop_value(loop_type, loop_value, target_task)
        vars_had_newline = self._set_vars(vars_, target_task)
        self._handle_last_key_newline(loop_had_newline or vars_had_newline, target_task)
        return True

    # flattend lookup is in the community.general collection (see note above)
    _replace_with_flattened = functools.partialmethod(
        _replace_with_items, flatten_levels=None
    )

    # noinspection PyUnusedLocal
    def _replace_with_indexed_items(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        templar: Templar,
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

        loop_value = filter_with_flatten(templar.environment, loop_value, levels=1)
        if loop_value is None:
            # unexpected template.
            # There shouldn't be TemplateData nodes or more than one expression.
            return False

        position = list(target_task.keys()).index(loop_type)

        loop_had_newline = self._set_loop_value(loop_type, loop_value, target_task)
        vars_had_newline = self._set_vars(vars_, target_task)

        if "loop_control" not in target_task:
            target_task.insert(position + 1, "loop_control", CommentedMap())
        elif not isinstance(target_task["loop_control"], MutableMapping):
            target_task["loop_control"] = CommentedMap()
        target_task["loop_control"]["index_var"] = index_var_name
        self._handle_last_key_newline(loop_had_newline or vars_had_newline, target_task)
        return True

    # noinspection PyUnusedLocal
    def _replace_with_together(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        templar: Templar,
    ) -> bool:
        with_together = target_task[loop_type]
        if not isinstance(with_together, MutableSequence):
            # this is probably an indirect set of lists stored in a variable somewhere.
            # we would need to parse the Jinja, and, if simple, check for that var
            # in vars. Then, if that is a list, continue.
            return False

        lists_count = len(with_together)
        if lists_count < 2:
            # not sure what to do with this
            return False

        jinja_env: Environment = templar.environment

        vars_ = None
        if all(
            isinstance(item, str) and templar.is_template(item)
            for item in with_together
        ):
            # all Jinja expressions, collapse them into one.
            with_together_asts = [
                jinja_env.parse(template) for template in with_together
            ]
            # we'll reuse the first template
            loop_ast = with_together_asts[0]
            loop_output_node = None
            with_together_nodes = []
            for ast in with_together_asts:
                output_node = cast(nodes.Output, ast.body[0])
                if loop_output_node is None:
                    loop_output_node = output_node
                if len(output_node.nodes) != 1:
                    # unexpected template.
                    # There shouldn't be TemplateData nodes or more than one expression.
                    return False
                node: nodes.Node = output_node.nodes[0]
                with_together_nodes.append(node)
            loop_output_node.nodes[0] = nodes.Filter(
                nodes.Filter(
                    with_together_nodes[0],
                    "zip_longest",
                    with_together_nodes[1:],
                    [],
                    None,
                    None,
                ),
                "list",
                [],
                [],
                None,
                None,
            )
        else:
            vars_ = target_task.get("vars", CommentedMap())
            var_name = self._unique_vars_name(vars_, "data")
            vars_[var_name] = with_together
            loop_ast = jinja_env.parse(
                "{{ " + var_name + "[0] | zip_longest(*" + var_name + "[1:]) | list }}"
            )

        loop_value = dump(node=loop_ast, environment=jinja_env)
        vars_had_newline = self._set_vars(vars_, target_task)
        loop_had_newline = self._set_loop_value(loop_type, loop_value, target_task)
        self._handle_last_key_newline(loop_had_newline or vars_had_newline, target_task)
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
