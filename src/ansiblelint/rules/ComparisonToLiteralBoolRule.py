# Copyright (c) 2016, Will Thames and contributors
# Copyright (c) 2018-2021, Ansible Project

import os
import re
from typing import Any, Dict, MutableSequence, Optional, Union

import py
from ansible.template import Templar
from jinja2 import nodes
from jinja2.environment import Environment
from jinja2.lexer import TOKEN_EQ, TOKEN_NE
from jinja2.visitor import NodeTransformer
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import AnsibleLintRule, TransformMixin
from ansiblelint.transform_utils import dump
from ansiblelint.utils import ansible_templar, nested_items


class CompareNodeTransformer(NodeTransformer):
    # noinspection PyMethodMayBeStatic
    def visit_Compare(self, node: nodes.Compare) -> Optional[nodes.Node]:
        left: nodes.Expr = node.expr
        if len(node.ops) > 1:
            # How do I transform a Compare with multiple Operands?
            # That does not make sense with !=,== bool, so just skip it.
            return self.generic_visit(node)

        operand: nodes.Operand = node.ops[0]
        op: str = operand.op
        right: nodes.Expr = operand.expr
        if not isinstance(right, nodes.Const):
            return self.generic_visit(node)

        exp = (op, right.value)
        if exp == (TOKEN_EQ, True) or exp == (TOKEN_NE, False):
            # var
            negate = False
        elif exp == (TOKEN_NE, True) or exp == (TOKEN_EQ, False):
            # not var
            negate = True
        else:
            return self.generic_visit(node)

        if negate:
            return self.generic_visit(nodes.Not(left, lineno=node.lineno))
        else:
            return self.generic_visit(left)


class ComparisonToLiteralBoolRule(AnsibleLintRule, TransformMixin):
    id = 'literal-compare'
    shortdesc = "Don't compare to literal True/False"
    description = (
        'Use ``when: var`` rather than ``when: var == True`` '
        '(or conversely ``when: not var``)'
    )
    transform_description = (
        "Comparing to literal True/False is unnecessary. This "
        "simplifies when conditions in playbooks to remove "
        "`== True` and replace `== False` with `not`."
    )
    severity = 'HIGH'
    tags = ['idiom']
    version_added = 'v4.0.0'

    literal_bool_compare = re.compile("[=!]= ?(True|true|False|false)")

    def matchtask(
        self, task: Dict[str, Any], file: Optional[Lintable] = None
    ) -> Union[bool, str]:
        for k, v, _ in nested_items(task):
            if k == 'when':
                if isinstance(v, str):
                    if self.literal_bool_compare.search(v):
                        return True
                elif isinstance(v, bool):
                    pass
                else:
                    for item in v:
                        if isinstance(item, str) and self.literal_bool_compare.search(
                            item
                        ):
                            return True

        return False

    def transform(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to fix the MatchError."""

        target_task: CommentedMap = self._seek(match.yaml_path, data)
        when = target_task["when"]
        when_is_list = isinstance(when, MutableSequence)

        if not when_is_list:
            when = [when]

        new_when = []
        for when_expr in when:
            ast = self._parse_when_expr(lintable.path, when_expr)
            updated_ast = CompareNodeTransformer().visit(ast)
            new_when.append(self._dump_when(lintable.path, updated_ast))

        if when_is_list:
            # This is not just a list. It is a ruamel.yaml CommentedSeq
            # Replacing the entire list and setting [:] both remove comments.
            # So, we replace each item in the list separately to preserve comments.
            for index, when_expr in enumerate(new_when):
                target_task["when"][index] = when_expr
        else:
            target_task["when"] = new_when[0]
        self._fixed(match)

    @staticmethod
    def _jinja_env(path: py.path.local) -> Environment:
        basedir: str = os.path.abspath(os.path.dirname(str(path)))
        templar: Templar = ansible_templar(basedir, templatevars={})
        jinja_env: Environment = templar.environment
        return jinja_env

    def _parse_when_expr(self, path: py.path.local, when: str) -> nodes.Template:
        expression = "{{" + when + "}}"
        ast = self._jinja_env(path).parse(expression)
        return ast

    def _dump_when(self, path: py.path.local, ast: nodes.Template):
        jinja_env = self._jinja_env(path)
        expression = dump(node=ast, environment=jinja_env)
        # remove "{{ " and " }}" (dump always adds space w/ braces)
        return expression[3:-3]
