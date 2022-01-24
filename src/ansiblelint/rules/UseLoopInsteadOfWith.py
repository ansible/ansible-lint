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

from ansible.parsing.splitter import parse_kv
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


def _get_sequence_params(with_sequence: str) -> Dict[str, Any]:
    # sadly we need to parse the with_sequence string
    # and there's a shortcut format for this!
    # we can't just import the lookup itself, because it expects
    # vars to already be templated. So we parse it ourselves
    from ansible.plugins.lookup.sequence import SHORTCUT

    match = SHORTCUT.match(with_sequence)
    params = {}
    if match:
        # shorthand mode. Assume
        (
            _,
            params["start"],
            params["end"],
            _,
            params["stride"],
            _,
            params["format"],
        ) = match.groups()
        for key in ["start", "end", "stride"]:
            try:
                value = int(params[key], 0)
            except ValueError:
                # might be a template string. leave as is.
                continue
            params[key] = value
    else:
        params = parse_kv(with_sequence)
        if "count" in params:
            count = params.pop("count")
            if count != 0:
                params["end"] = (
                    params.get("start", 1) + count * params.get("stride", 1) - 1
                )
            else:
                params["start"] = 0
                params["end"] = 0
                params["stride"] = 0
        if "stride" in params and "start" not in params:
            params["start"] = 0
    return params


def _get_node(template: str, jinja_env: Environment):
    """Get the node from the template, discarding Template and Output nodes."""
    ast = jinja_env.parse(template)
    output_node = cast(nodes.Output, ast.body[0])
    if len(output_node.nodes) != 1:
        # unexpected template.
        # There shouldn't be TemplateData nodes or more than one expression.
        return None
    return output_node.nodes[0]


def _get_empty_ast(jinja_env: Environment) -> Tuple[nodes.Template, nodes.Output]:
    """Get an empty template ast."""
    ast = jinja_env.parse("{{ discard_me }}")
    output_node = cast(nodes.Output, ast.body[0])
    output_node.nodes.clear()
    return ast, output_node


def filter_with_flatten(
    jinja_env: Environment, loop_value: str, levels: int = None
) -> Optional[str]:
    """Edit the given template to apply the 'flatten' filter to it."""
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


def filter_with_dict2items(jinja_env: Environment, loop_value: str) -> Optional[str]:
    """Edit the given template to apply the 'dict2items' filter to it."""
    loop_ast = jinja_env.parse(loop_value)
    output_node = cast(nodes.Output, loop_ast.body[0])
    if len(output_node.nodes) != 1:
        # unexpected template.
        # There shouldn't be TemplateData nodes or more than one expression.
        return None
    node: nodes.Node = output_node.nodes[0]
    output_node.nodes[0] = nodes.Filter(node, "dict2items", [], [], None, None)
    return dump(node=loop_ast, environment=jinja_env)


class SimpleNodeReplacer(NodeTransformer):
    """This Jinja Node Replacer can only handle simple (hashable) nodes.

    Nodes that have list or dict attributes will not work.
    """

    def __init__(self, translate: Dict[str, str]):
        """Initialize the SingleNodeReplacer with the map of which nodes to replace."""
        templar = ansible_templar(".", templatevars={})
        jinja_env = templar.environment
        key_asts = [
            _get_node(
                key if templar.is_possibly_template(key) else "{{" + key + "}}",
                jinja_env,
            )
            for key in translate.keys()
        ]
        value_asts = [
            _get_node(
                value if templar.is_possibly_template(value) else "{{" + value + "}}",
                jinja_env,
            )
            for value in translate.values()
        ]
        self.translate = {
            self._hash(key_ast): value_ast
            for key_ast, value_ast in zip(key_asts, value_asts)
        }

    def _hash(self, node: nodes.Node):
        # we cannot rely on Jinja's hashing behavior (node.__hash__).
        # It worked from 3.0.0-3.0.2, but Jinja 3.0.3 reverted to using
        # the object id for the hash. So, we recreate the 3.0.0 hashing
        # behavior here. This only works for simple nodes. If any of
        # the node's fields are lists, then hashing won't work.
        return hash(
            tuple(
                (field, self._hash(value) if isinstance(value, nodes.Node) else value)
                for field, value in node.iter_fields()
            )
        )

    def visit(self, node: nodes.Node, *args: Any, **kwargs: Any) -> Any:
        try:
            node_hash = self._hash(node)
            if node_hash in self.translate:
                return self.translate[node_hash]
        except TypeError:
            # got a complex node where hashing does not work. Ignore.
            pass
        return super().visit(node, *args, **kwargs)


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

    # NB: Some lookups are in the community.general collection: flattened, cartesian
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

    def _translate_vars_in_task(
        self,
        translate: Dict[str, str],
        loop_type: str,
        module: str,
        target_task: CommentedMap,
        templar: Templar,
    ):
        jinja_env: Environment = templar.environment
        var_replacer = SimpleNodeReplacer(translate=translate)
        # look for places to replace index_var and item_var
        for key, value, parent_path in nested_items_path(target_task):
            top_key = parent_path[0] if parent_path else None
            if (
                # The loop definition gets templated before the loop (of course),
                # so do not look for loop_var or index_var usage there.
                {key, top_key} & {loop_type, "loop"}
                # Under loop_control, these are also templated before the loop:
                or (
                    top_key == "loop_control"
                    and key in ("loop_var", "index_var", "loop_pause", "extended")
                )
                # we are only looking for template strings
                or not isinstance(value, str)
            ):
                continue
            do_wrap_template = (
                not parent_path and (key == "when" or key.endswith("_when"))
            ) or (
                parent_path
                and parent_path[-1] == module
                and module in ("debug", "ansible.builtin.debug")
                and key == "var"
            )
            if not do_wrap_template and not templar.is_template(value):
                continue
            template = "{{" + value + "}}" if do_wrap_template else value
            ast = jinja_env.parse(template)
            ast = var_replacer.visit(ast)
            new_template = cast(str, dump(node=ast, environment=jinja_env))
            if do_wrap_template:
                # remove "{{ " and " }}" (dump always adds space w/ braces)
                new_template = new_template[3:-3]

            self._seek(parent_path, target_task)[key] = new_template

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

    # flattened lookup is in the community.general collection (see note above)
    _replace_with_flattened = functools.partialmethod(
        _replace_with_items, flatten_levels=None
    )

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

        index_var_name = target_task.get("loop_control", {}).get(
            "index_var", self._unique_vars_name(vars_, "index")
        )
        loop_var_name = target_task.get("loop_control", {}).get(
            "loop_var", self._unique_vars_name(vars_, "item")
        )

        loop_value = filter_with_flatten(templar.environment, loop_value, levels=1)
        if loop_value is None:
            # unexpected template.
            # There shouldn't be TemplateData nodes or more than one expression.
            return False

        self._translate_vars_in_task(
            translate={
                f"{loop_var_name}.0": index_var_name,
                f"{loop_var_name}.1": loop_var_name,
            },
            loop_type=loop_type,
            module=task["action"]["__ansible_module_original__"],
            target_task=target_task,
            templar=templar,
        )

        position = list(target_task.keys()).index(loop_type)

        loop_had_newline = self._set_loop_value(loop_type, loop_value, target_task)
        vars_had_newline = self._set_vars(vars_, target_task)

        if "loop_control" not in target_task:
            target_task.insert(position + 1, "loop_control", CommentedMap())
        elif not isinstance(target_task["loop_control"], MutableMapping):
            target_task["loop_control"] = CommentedMap()
        target_task["loop_control"]["index_var"] = index_var_name
        if loop_var_name != "item":
            target_task["loop_control"]["loop_var"] = loop_var_name
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
            # collapse all Jinja expressions into one ast
            loop_ast, loop_output_node = _get_empty_ast(jinja_env)
            with_together_nodes = [
                _get_node(template, jinja_env) for template in with_together
            ]
            if any(node is None for node in with_together_nodes):
                # unexpected template.
                # There shouldn't be TemplateData nodes or more than one expression.
                return False

            loop_output_node.nodes.append(
                nodes.Filter(
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

    # noinspection PyUnusedLocal
    def _replace_with_dict(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        templar: Templar,
    ) -> bool:
        with_dict = target_task[loop_type]
        vars_ = None
        if isinstance(with_dict, CommentedMap):
            vars_ = target_task.get("vars", CommentedMap())
            var_name = self._unique_vars_name(vars_, "items")
            vars_[var_name] = with_dict

            loop_value = "{{" + var_name + "}}"
        else:
            loop_value = with_dict

        loop_value = filter_with_dict2items(templar.environment, loop_value)
        if loop_value is None:
            # unexpected template.
            # There shouldn't be TemplateData nodes or more than one expression.
            return False

        loop_had_newline = self._set_loop_value(loop_type, loop_value, target_task)
        vars_had_newline = self._set_vars(vars_, target_task)
        self._handle_last_key_newline(loop_had_newline or vars_had_newline, target_task)
        return True

    def _replace_with_sequence(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        templar: Templar,
    ) -> bool:
        with_sequence: str = target_task[loop_type]
        if not isinstance(with_sequence, str):
            # what? This should be a string... giving up!
            return False

        params = _get_sequence_params(with_sequence)
        try:
            adjust = "+ 1" if 0 <= int(params.get("stride", 1), 0) else "- 1"
        except ValueError:
            # probably a template
            adjust = "+ 1"

        loop_value = "{{ range("
        if "start" in params:
            loop_value += f"{params['start']}, "
        loop_value += f"{params['end']} {adjust}"
        if "stride" in params:
            loop_value += f", {params['stride']}"
        loop_value += ") | list }}"

        if "format" in params:
            vars_ = target_task.get("vars", CommentedMap())
            loop_var_name = target_task.get("loop_control", {}).get(
                "loop_var", self._unique_vars_name(vars_, "item")
            )
            # search for the item var and replace it with
            self._translate_vars_in_task(
                translate={
                    loop_var_name: f"'{params['format']}' | format({loop_var_name})"
                },
                loop_type=loop_type,
                module=task["action"]["__ansible_module_original__"],
                target_task=target_task,
                templar=templar,
            )
            if loop_var_name != "item":
                if "loop_control" not in target_task:
                    position = list(target_task.keys()).index(loop_type)
                    target_task.insert(position + 1, "loop_control", CommentedMap())
                elif not isinstance(target_task["loop_control"], MutableMapping):
                    target_task["loop_control"] = CommentedMap()
                target_task["loop_control"]["loop_var"] = loop_var_name

        loop_had_newline = self._set_loop_value(loop_type, loop_value, target_task)
        # do not set vars_ here. We queried but did not modify it.
        self._handle_last_key_newline(loop_had_newline, target_task)
        return True

    # noinspection PyUnusedLocal
    def _replace_with_subelements(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        templar: Templar,
    ) -> bool:
        with_subelements: CommentedSeq = target_task[loop_type]
        if (
            # This might be a string template referring to a
            # variable that is who-knows-where.
            not isinstance(with_subelements, CommentedSeq)
            # Or it is a list with the wrong number of elements.
            or not 2 <= len(with_subelements) <= 3
            # Or the subelements_path is an unknown type
            or not isinstance(with_subelements[1], str)
        ):
            return False
        subelements_items = with_subelements[0]
        subelements_path = with_subelements[1]
        try:
            subelements_skip_missing = with_subelements[2]
            subelements_skip_missing = subelements_skip_missing["skip_missing"]
        except (IndexError, KeyError):
            subelements_skip_missing = None

        vars_ = None
        jinja_env: Environment = templar.environment
        if isinstance(subelements_items, str):
            # got a template
            loop_value = subelements_items
        else:
            # got a raw list. Move it to 'vars:'
            vars_ = target_task.get("vars", CommentedMap())
            var_name = self._unique_vars_name(vars_, "items")
            vars_[var_name] = subelements_items
            loop_value = "{{" + var_name + "}}"

        args = [
            _get_node(
                subelements_path
                if templar.is_template(subelements_path)
                else "{{" + repr(subelements_path) + "}}",
                jinja_env,
            )
        ]
        if args[0] is None:
            return False

        if subelements_skip_missing is None:
            kwargs = []
        else:
            kwarg = _get_node(
                subelements_skip_missing
                if templar.is_template(subelements_skip_missing)
                else "{{" + repr(subelements_skip_missing) + "}}",
                jinja_env,
            )
            if kwarg is None:
                return False
            kwargs = [nodes.Keyword("skip_missing", kwarg)]

        loop_ast = jinja_env.parse(loop_value)
        output_node = cast(nodes.Output, loop_ast.body[0])
        if len(output_node.nodes) != 1:
            # unexpected template.
            # There shouldn't be TemplateData nodes or more than one expression.
            return False
        node: nodes.Node = output_node.nodes[0]

        output_node.nodes[0] = nodes.Filter(
            node, "subelements", args, kwargs, None, None
        )
        loop_value = cast(str, dump(node=loop_ast, environment=jinja_env))

        loop_had_newline = self._set_loop_value(loop_type, loop_value, target_task)
        vars_had_newline = self._set_vars(vars_, target_task)
        self._handle_last_key_newline(loop_had_newline or vars_had_newline, target_task)
        return True

    # noinspection PyUnusedLocal
    def _replace_with_nested(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        templar: Templar,
    ) -> bool:
        with_nested = target_task[loop_type]
        if not isinstance(with_nested, CommentedSeq):
            # probably a template referring to a var from who knows where.
            return False
        jinja_env: Environment = templar.environment
        vars_ = None
        nested_list_templates = []
        for index, nested_list in enumerate(with_nested):
            if isinstance(nested_list, str):
                if not templar.is_template(nested_list):
                    # strings should be templates. Bail out.
                    return False
                nested_list_templates.append(nested_list)
                continue
            # not a template. We need to put it in vars.
            if vars_ is None:
                vars_ = target_task.get("vars", CommentedMap())
            var_name = self._unique_vars_name(vars_, f"list{index}")
            vars_[var_name] = nested_list
            nested_list_templates.append("{{" + var_name + "}}")
        loop_ast, loop_output_node = _get_empty_ast(jinja_env)
        nested_list_nodes = [
            _get_node(template, jinja_env) for template in nested_list_templates
        ]
        if any(node is None for node in nested_list_nodes):
            # unexpected template.
            # There shouldn't be TemplateData nodes or more than one expression.
            return False
        loop_output_node.nodes.append(
            nodes.Filter(
                nodes.Filter(
                    nested_list_nodes[0],
                    "product",
                    nested_list_nodes[1:],
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
        )
        loop_value = cast(str, dump(node=loop_ast, environment=jinja_env))
        loop_had_newline = self._set_loop_value(loop_type, loop_value, target_task)
        vars_had_newline = self._set_vars(vars_, target_task)
        self._handle_last_key_newline(loop_had_newline or vars_had_newline, target_task)
        return True

    # cartesian lookup is in the community.general collection (see note above)
    _replace_with_cartesian = _replace_with_nested

    def _replace_with_random_choice(
        self,
        loop_type: str,
        task: Dict[str, Any],
        target_task: CommentedMap,
        templar: Templar,
    ) -> bool:
        with_random_choice = target_task[loop_type]
        vars_ = target_task.get("vars", CommentedMap())
        if isinstance(with_random_choice, list):
            var_name = self._unique_vars_name(vars_, "choices")
            vars_[var_name] = with_random_choice
            loop_value = "{{" + var_name + "}}"
        else:
            loop_value = with_random_choice
        loop_var_name = target_task.get("loop_control", {}).get(
            "loop_var", self._unique_vars_name(vars_, "item")
        )
        jinja_env = templar.environment
        ast, output_node = _get_empty_ast(jinja_env)
        node = _get_node(loop_value, jinja_env)
        output_node.nodes.append(nodes.Filter(node, "random", [], [], None, None))
        template = cast(str, dump(node=ast, environment=jinja_env))
        self._translate_vars_in_task(
            translate={
                loop_var_name: template,
            },
            loop_type=loop_type,
            module=task["action"]["__ansible_module_original__"],
            target_task=target_task,
            templar=templar,
        )
        if not vars_:
            vars_ = None

        vars_had_newline = self._set_vars(vars_, target_task)
        # This is not really a loop, but we'll use _set_loop_value to see if we need a newline.
        loop_had_newline = self._set_loop_value(loop_type, None, target_task)
        loop_control_had_newline = False
        if "loop_control" in target_task:
            loop_control_had_newline = self._set_loop_value(
                "loop_control", None, target_task
            )
        target_task.pop("loop", None)
        self._handle_last_key_newline(
            vars_had_newline or loop_had_newline or loop_control_had_newline,
            target_task,
        )
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
