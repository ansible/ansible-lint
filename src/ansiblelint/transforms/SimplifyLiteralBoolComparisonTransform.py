import os
from typing import List, Tuple, Union

import py
from ansible.template import Templar
from jinja2 import nodes
from jinja2.environment import Environment
from jinja2.lexer import (
    ignored_tokens,
    TOKEN_OPERATOR,
    TOKEN_NAME,
    TOKEN_EQ,
    TOKEN_NE,
    TOKEN_WHITESPACE,
)
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.ComparisonToLiteralBoolRule import ComparisonToLiteralBoolRule
from ansiblelint.transforms import Transform
from ansiblelint.utils import ansible_templar


class SimplifyLiteralBoolComparisonTransform(Transform):
    id = "literal-bool-comparison"
    shortdesc = "Simplify literal bool comparisons in when conditions."
    description = (
        "Comparing to literal True/False is unnecessary. This "
        "simplifies when conditions in playbooks to remove "
        "`== True` and replace `== False` with `not`."
    )
    version_added = "5.3"

    wants = ComparisonToLiteralBoolRule
    tags = ComparisonToLiteralBoolRule.tags

    def __call__(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq],
    ) -> None:
        """Transform data to fix the MatchError."""

        target_task: dict = self._seek(match.yaml_path, data)
        when = target_task["when"]
        tokens, ast = self._parse_when(lintable.path, when)
        tokens = self._transform(tokens, ast)
        target_task["when"] = self._concat_tokens(tokens)
        self._fixed(match)

    @staticmethod
    def _concat_tokens(tokens: List[Tuple[int, str, str]]) -> str:
        output = "".join(value for _, _, value in tokens)
        return output

    @staticmethod
    def _parse_when(
        path: py.path.local, when: str
    ) -> Tuple[List[Tuple[int, str, str]], nodes.Template]:
        basedir: str = os.path.abspath(os.path.dirname(str(path)))
        templar: Templar = ansible_templar(basedir, templatevars={})
        jinja_env: Environment = templar.environment

        expression = "{{" + when + "}}"
        tokens = list(jinja_env.lex(expression))

        # tokens = [
        #   # line_number, token_type, value
        #   (1, 'variable_begin', '{{'),
        #   (1, 'name', 'my_var'),
        #   (1, 'whitespace', ' '),
        #   (1, 'operator', '=='),
        #   (1, 'whitespace', ' '),
        #   (1, 'name', 'True'),
        #   (1, 'variable_end', '}}')
        # ]

        # strip start/end tokens {{ and }}
        tokens = tokens[1:-1]

        ast = jinja_env.parse(expression)
        return tokens, ast

    def _transform(self, tokens: List[Tuple[int, str, str]], ast: nodes.Template):
        for compare_node in ast.find_all(nodes.Compare):
            left: nodes.Expr = compare_node.ops[0].expr
            op: str = compare_node.ops[0].op
            right: nodes.Expr = compare_node.ops[0].expr
            if not isinstance(right, nodes.Const):
                continue
            right: str = right.value

            exp = (op, right.lower())
            if exp == (TOKEN_EQ, "true") or exp == (TOKEN_NE, "false"):
                # var
                negate = False
            elif exp == (TOKEN_NE, "true") or exp == (TOKEN_EQ, "false"):
                # not var
                negate = True
            else:
                continue
            tokens = self._transform_var(tokens, negate, left, op, right)
        return tokens

    def _transform_var(
        self,
        tokens: List[Tuple[int, str, str]],
        negate: bool,
        left: nodes.Expr,
        op: str,
        right: str,
    ):
        last = None
        found_left = found_op = found_right = False
        left_index = 0
        delete_start_index = None
        delete_stop_index = None
        for i, (_, token_type, value) in enumerate(tokens[:]):
            if token_type in ignored_tokens:
                last = (i, token_type, value)
                continue
            if not found_left and token_type == TOKEN_NAME:
                # TODO: identify left
                # TODO: method to compile Expr ast to lex tokens
                if True:
                    found_left = True
                    left_index = i
                last = None
                continue
            elif found_left and token_type == TOKEN_OPERATOR and value == op:
                found_op = True
                delete_start_index = last[0] if last else i
                last = None
                continue
            elif found_op and token_type == TOKEN_NAME and value.lower() == right.lower():
                found_right = True
                delete_stop_index = i
                break
            elif found_op and token_type == TOKEN_NAME:
                found_op = False
            else:
                last = None
        if not found_right:
            # this should not happen
            return tokens
        tokens = tokens[:delete_start_index] + tokens[delete_stop_index+1:]
        if negate:
            tokens.insert(left_index, (1, TOKEN_WHITESPACE, " "))
            tokens.insert(left_index, (1, TOKEN_NAME, "not"))
        return tokens
