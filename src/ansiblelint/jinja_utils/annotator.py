"""Jinja AST whitespace annotator."""

from contextlib import contextmanager
from typing import Any, List, Optional, Tuple, Union, cast

from jinja2 import lexer as j2tokens, nodes
from jinja2.compiler import operators as operands
from jinja2.environment import Environment
from jinja2.visitor import NodeVisitor

from .token import pre_iter_normalize_newlines, Token, Tokens


def annotate(
    node: nodes.Template,
    environment: Environment,
    raw_template: str,
) -> nodes.Template:
    """Annotate a jinja2 AST with info about whitespace.

    This is based on jinja2.compiler.generate
    """
    if not isinstance(node, nodes.Template):
        raise TypeError("Can't dump non template nodes")

    annotator = NodeAnnotator(environment, raw_template)
    annotator.visit(node)

    return node


# Ignore these because they're required by Jinja2's NodeVisitor interface
# pylint: disable=too-many-public-methods,invalid-name
class NodeAnnotator(NodeVisitor):
    """Annotate a jinja2 AST with info about whitespace."""

    def __init__(
        self,
        environment: Environment,
        raw_template: str,
    ):
        """Create a TemplateDumper."""
        self.environment = environment
        # Jinja lexes a standardized stream with \n
        self.stream = pre_iter_normalize_newlines(
            raw_template, environment.keep_trailing_newline
        )
        # We need to go through all the tokens to populate the token pair details
        self.tokens = Tokens(environment.lexer, raw_template)

    # -- Seek Helpers

    def seek_past(self, token_type: str, *values: str) -> None:
        """Seek past a series of tokens of the same type."""
        for value in values:
            self.tokens.seek(token_type, value)
        else:
            self.tokens.seek(token_type)

    # -- Annotation Helpers

    def annotate(
        self,
        node: nodes.Node,
        *,
        start: int,
        end: int,
    ) -> None:
        node.tokens = self.tokens[start:end]

    def get_chomp_index(self, pre_tokens: List[Token]) -> int:
        whitespace_tokens = []
        for token in reversed(pre_tokens):
            if token.jinja_token is None:
                whitespace_tokens.append(token)
            else:
                break
        return whitespace_tokens[-1].index

    @contextmanager
    def token_pair_block(self, node: nodes.Node, *names: str):
        pre_tokens, start_token = self.tokens.seek(j2tokens.TOKEN_BLOCK_BEGIN)
        # bypass each of the block's names
        self.seek_past(j2tokens.TOKEN_NAME, *names)
        stop_token = start_token.pair
        if hasattr(node, "tokens"):
            # some nodes consist of multiple blocks. In that case, just extend the end.
            start_index = node.tokens[0]
        elif start_token.chomp:
            start_index = self.get_chomp_index(pre_tokens)
        else:
            start_index = start_token.index

        yield pre_tokens, start_token, stop_token

        stop_index = stop_token.index
        assert self.tokens.index <= stop_index  # how could child nodes pass the end token?!
        self.tokens.index = stop_index
        node.tokens = (start_index, stop_index)

    @contextmanager
    def token_pair_variable(self, node: nodes.Node):
        pre_tokens, start_token = self.tokens.seek(j2tokens.TOKEN_VARIABLE_BEGIN)
        stop_token = start_token.pair
        if start_token.chomp:
            start_index = self.get_chomp_index(pre_tokens)
        else:
            start_index = start_token.index

        yield pre_tokens, start_token, stop_token

        stop_index = stop_token.index
        assert self.tokens.index <= stop_index  # how could child nodes pass the end token?!
        self.tokens.index = stop_index
        node.tokens = (start_index, stop_index)

    def token_pair_expression(self, node: nodes.Node, left_token: str):
        pre_tokens, start_token = self.tokens.seek(left_token)
        stop_token = start_token.pair
        if hasattr(node, "tokens"):
            # some nodes consist of multiple blocks. In that case, just extend the end.
            start_index = node.tokens[0]
        else:
            start_index = start_token.index

        yield pre_tokens, start_token, stop_token

        stop_index = stop_token.index
        assert self.tokens.index <= stop_index  # how could child nodes pass the end token?!
        self.tokens.index = stop_index
        node.tokens = (start_index, stop_index)

    # -- Various compilation helpers

    def signature(
        self,
        node: Union[nodes.Call, nodes.Filter, nodes.Test],
    ) -> None:
        """Write a function call to the stream for the current node."""
        with self.token_pair_expression(node, j2tokens.TOKEN_LPAREN):
            first = True
            arg: nodes.Expr
            for arg in node.args:
                if first:
                    first = False
                else:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(arg, parent=node)
            # cast because typehint is incorrect on nodes._FilterTestCommon
            for kwarg in cast(List[nodes.Keyword], node.kwargs):
                if first:
                    first = False
                else:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(kwarg, parent=node)
            if node.dyn_args:
                if first:
                    first = False
                else:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.tokens.seek(j2tokens.TOKEN_MUL)
                self.visit(node.dyn_args, parent=node)
            if node.dyn_kwargs is not None:
                if first:
                    first = False
                else:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.tokens.seek(j2tokens.TOKEN_POW)
                self.visit(node.dyn_kwargs, parent=node)

    def macro_signature(
        self,
        node: Union[nodes.Macro, nodes.CallBlock],
    ) -> None:
        """Write a Macro or CallBlock signature to the stream for the current node."""
        with self.token_pair_expression(node, j2tokens.TOKEN_LPAREN):
            for idx, arg in enumerate(node.args):
                if idx:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(arg, parent=node)
                try:
                    default = node.defaults[idx - len(node.args)]
                except IndexError:
                    continue
                self.tokens.seek(j2tokens.TOKEN_ASSIGN)
                self.visit(default, parent=node)

    # -- Statement Visitors

    def visit_Template(self, node: nodes.Template) -> None:
        """Template is the root node."""
        initial_token = next(self.tokens)
        self.generic_visit(node)
        eof_token = next(self.tokens)
        # TODO: better way to ensure all tokens have been consumed?
        assert self.tokens.end
        self.annotate(node, start=initial_token.start_pos, end=eof_token.end_pos)

    def generic_visit(self, node: nodes.Node, *args: Any, **kwargs: Any) -> Any:
        """Called if no explicit visitor function exists for a node."""
        for child_node in node.iter_child_nodes():
            self.visit(child_node, parent=node, *args, **kwargs)

    def visit_Output(self, node: nodes.Output, parent: nodes.Node) -> None:
        """Visit an ``Output`` node in the stream.

        Output is a ``{{ }}`` statement (aka ``print`` or output statement).
        """
        for child_node in node.iter_child_nodes():
            child_node.parent = node
            # child_node might be TemplateData which is outside {{ }}
            if isinstance(child_node, nodes.TemplateData):
                self.visit(child_node, parent=node)
                continue

            # child_node is one of the expression nodes surrounded by {{ }}
            with self.token_pair_variable(child_node) as (
                pre_tokens,
                start_token,
                stop_token,
            ):
                self.visit(child_node, parent=node)

    def visit_Block(self, node: nodes.Block, parent: nodes.Node) -> None:
        """Visit a ``Block`` in the stream.

        Examples::

            {% block name %}block{% endblock %}
            {% block name scoped %}block{% endblock %}
            {% block name scoped required %}block{% endblock %}
            {% block name required %}block{% endblock %}
        """
        block_name_tokens: List[str] = ["block", node.name]
        # jinja parser only supports one order: scoped required
        if node.scoped:
            block_name_tokens.append("scoped")
        if node.required:
            block_name_tokens.append("required")
        with self.token_pair_block(node, *block_name_tokens) as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endblock") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    def visit_Extends(self, node: nodes.Extends, parent: nodes.Node) -> None:
        """Visit an ``Extends`` block in the stream.

        Example::

            {% extends name %}
        """
        with self.token_pair_block(node, "extends") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.template, parent=node)

    def visit_Include(self, node: nodes.Include, parent: nodes.Node) -> None:
        """Visit an ``Include`` block in the stream.

        Examples::

            {% include name %}
            {% include name ignore missing %}
            {% include name ignore missing without context %}
            {% include name without context %}
        """
        with self.token_pair_block(node, "include") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.template, parent=node)
            if node.ignore_missing:
                self.seek_past(j2tokens.TOKEN_NAME, "ignore", "missing")
            # include defaults to "with context"
            index = self._index
            if not node.with_context:
                self.seek_past(j2tokens.TOKEN_NAME, "without", "context")
            elif "with" == self.stream[index : index + 4]:  # TODO: how to peek for with
                # with context (implicit default) explicitly specified
                self.seek_past(j2tokens.TOKEN_NAME, "with", "context")

    def visit_Import(self, node: nodes.Import, parent: nodes.Node) -> None:
        """Visit an ``Import`` block in the stream.

        Examples::

            {% import expr as name %}
            {% import expr as name without context %}
        """
        with self.token_pair_block(node, "import") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.template, parent=node)
            self.seek_past(j2tokens.TOKEN_NAME, "as", node.target)
            # import defaults to "without context"
            index = self._index
            if node.with_context:
                self.seek_past(j2tokens.TOKEN_NAME, "with", "context")
            elif "without" == self.stream[index : index + 7]:  # TODO: how to peek for without
                # without context (implicit default) explicitly specified
                self.seek_past(j2tokens.TOKEN_NAME, "without", "context")

    def visit_FromImport(self, node: nodes.FromImport, parent: nodes.Node) -> None:
        """Visit a ``FromImport`` block in the stream.

        Examples::

            {% from expr import expr as name %}
            {% from expr import expr as name without context %}
        """
        with self.token_pair_block(node, "from") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.template, parent=node)
            self.tokens.seek(j2tokens.TOKEN_NAME, "import")
            for idx, name in enumerate(node.names):
                if idx:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                if isinstance(name, tuple):
                    self.seek_past(j2tokens.TOKEN_NAME, name[0], "as", name[1])
                else:  # str
                    self.tokens.seek(j2tokens.TOKEN_NAME, name)
                # TODO: trailing comma?
            index = self._index
            # import defaults to "without context"
            if node.with_context:
                self.seek_past(j2tokens.TOKEN_NAME, "with", "context")
            elif "without" == self.stream[index : index + 7]:  # TODO: how to peek for without
                # without context (implicit default) explicitly specified
                self.seek_past(j2tokens.TOKEN_NAME, "without", "context")

    def visit_For(self, node: nodes.For, parent: nodes.Node) -> None:
        """Visit a ``For`` block in the stream.

        Examples::

            {% for target in iter %}block{% endfor %}
            {% for target in iter recursive %}block{% endfor %}
            {% for target in iter %}block{% else %}block{% endfor %}
        """
        with self.token_pair_block(node, "for") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.target, parent=node)
            self.tokens.seek(j2tokens.TOKEN_NAME, "in")
            self.visit(node.iter, parent=node)
            if node.test is not None:
                self.tokens.seek(j2tokens.TOKEN_NAME, "if")
                self.visit(node.test, parent=node)
            if node.recursive:
                self.tokens.seek(j2tokens.TOKEN_NAME, "recursive")
        for child_node in node.body:
            self.visit(child_node, parent=node)
        if node.else_:
            with self.token_pair_block(node, "else") as (
                pre_tokens,
                start_token,
                stop_token,
            ):
                pass
            for child_node in node.else_:
                self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endfor") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    def visit_If(self, node: nodes.If, parent: nodes.Node) -> None:
        """Visit an ``If`` block in the stream."""
        with self.token_pair_block(node, "if") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.test, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        for elif_node in node.elif_:
            with self.token_pair_block(node, "elif") as (
                pre_tokens,
                start_token,
                stop_token,
            ):
                self.visit(elif_node.test, parent=node)
            for child_node in elif_node.body:
                self.visit(child_node, parent=node)
        if node.else_:
            with self.token_pair_block(node, "else") as (
                pre_tokens,
                start_token,
                stop_token,
            ):
                pass
            for child_node in node.else_:
                self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endif") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    def visit_With(self, node: nodes.With, parent: nodes.Node) -> None:
        """Visit a ``With`` statement (manual scopes) in the stream."""
        with self.token_pair_block(node, "with") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            first = True
            for target, expr in zip(node.targets, node.values):
                if first:
                    first = False
                else:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(target, parent=node)
                self.tokens.seek(j2tokens.TOKEN_ASSIGN)
                self.visit(expr, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endwith") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    def visit_ExprStmt(self, node: nodes.ExprStmt, parent: nodes.Node) -> None:
        """Visit a ``do`` block in the stream.

        ExprStmtExtension
            A ``do`` tag is like a ``print`` statement but doesn't print the return value.
        ExprStmt
            A statement that evaluates an expression and discards the result.
        """
        with self.token_pair_block(node, "do") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.node, parent=node)

    def visit_Assign(self, node: nodes.Assign, parent: nodes.Node) -> None:
        """Visit an ``Assign`` statement in the stream.

        Example::

            {% set var = value %}
        """
        with self.token_pair_block(node, "set") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.target, parent=node)
            self.tokens.seek(j2tokens.TOKEN_ASSIGN)
            self.visit(node.node, parent=node)

    # noinspection DuplicatedCode
    def visit_AssignBlock(self, node: nodes.AssignBlock, parent: nodes.Node) -> None:
        """Visit an ``Assign`` block in the stream.

        Example::

            {% set var %}value{% endset %}
        """
        with self.token_pair_block(node, "set") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.target, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endset") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    # noinspection DuplicatedCode
    def visit_FilterBlock(self, node: nodes.FilterBlock, parent: nodes.Node) -> None:
        """Visit a ``Filter`` block in the stream.

        Example::

            {% filter <filter> %}block{% endfilter %}
        """
        with self.token_pair_block(node, "filter") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(node.filter, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endfilter") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    def visit_Macro(self, node: nodes.Macro, parent: nodes.Node) -> None:
        """Visit a ``Macro`` definition block in the stream.

        Example::

            {% macro name(args/defaults) %}block{% endmacro %}
        """
        with self.token_pair_block(node, "macro", node.name) as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.macro_signature(node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endmacro") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    def visit_CallBlock(self, node: nodes.CallBlock, parent: nodes.Node) -> None:
        """Visit a macro ``Call`` block in the stream.

        Examples::

            {% call macro() %}block{% endcall %}
            {% call(args/defaults) macro() %}block{% endcall %}
        """
        with self.token_pair_block(node, "call") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            if node.args:
                self.macro_signature(node)
            self.visit(node.call, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endcall") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    # -- Expression Visitors

    def visit_Name(self, node: nodes.Name, parent: nodes.Node) -> None:
        """Visit a ``Name`` expression in the stream."""
        # ctx is one of: load, store, param
        # load named var, store named var, or store named function parameter
        self.tokens.seek(j2tokens.TOKEN_NAME, node.name)

    def visit_NSRef(self, node: nodes.NSRef, parent: nodes.Node) -> None:
        """Visit a ref to namespace value assignment in the stream."""
        self.tokens.seek(j2tokens.TOKEN_NAME, node.name)
        self.tokens.seek(j2tokens.TOKEN_DOT)
        self.tokens.seek(j2tokens.TOKEN_NAME, node.attr)

    def visit_Const(self, node: nodes.Const, parent: nodes.Node) -> None:
        """Visit a constant value (``int``, ``str``, etc) in the stream."""
        # We are using repr() here to handle quoting strings.
        # TODO: handle alt quotes
        self.tokens.seek(j2tokens.TOKEN_INTEGER, repr(node.value))
        self.tokens.seek(j2tokens.TOKEN_FLOAT, repr(node.value))
        self.tokens.seek(j2tokens.TOKEN_STRING, repr(node.value))

    def visit_TemplateData(self, node: nodes.TemplateData, parent: nodes.Node) -> None:
        """a constant string (between Jinja blocks)."""
        self.tokens.seek(j2tokens.TOKEN_DATA, node.data)

    def visit_Tuple(self, node: nodes.Tuple, parent: nodes.Node) -> None:
        """Visit a ``Tuple`` in the stream."""
        # TODO: handle ctx = load or store
        with self.token_pair_expression(node, j2tokens.TOKEN_LPAREN):
            for idx, item in enumerate(node.items):
                if idx:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(item, parent=node)
            if self.stream[self._index] == j2tokens.TOKEN_COMMA:
                self.tokens.seek(j2tokens.TOKEN_COMMA)

    def visit_List(self, node: nodes.List, parent: nodes.Node) -> None:
        """Visit a ``List`` in the stream."""
        with self.token_pair_expression(node, j2tokens.TOKEN_LBRACKET):
            for idx, item in enumerate(node.items):
                if idx:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(item, parent=node)
            if self.stream[self._index] == j2tokens.TOKEN_COMMA:
                self.tokens.seek(j2tokens.TOKEN_COMMA)

    def visit_Dict(self, node: nodes.Dict, parent: nodes.Node) -> None:
        """Visit a ``Dict`` in the stream."""
        with self.token_pair_expression(node, j2tokens.TOKEN_LBRACE):
            item: nodes.Pair
            for idx, item in enumerate(node.items):
                if idx:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(item.key, parent=node)
                self.tokens.seek(j2tokens.TOKEN_COLON)
                self.visit(item.value, parent=node)
            if self.stream[self._index] == j2tokens.TOKEN_COMMA:
                self.tokens.seek(j2tokens.TOKEN_COMMA)

    def _binary_op(self, node: nodes.BinExpr, parent: nodes.Node) -> None:
        """Visit a ``BinExpr`` (left and right op) in the stream."""
        # parentheses might be captured in whitespace

        self.visit(node.left, parent=node)

        try:
            op_token = j2tokens.operators[node.operator]
        except KeyError:
            self.tokens.seek(j2tokens.TOKEN_NAME, node.operator)  # and, or
        else:
            self.tokens.seek(op_token)

        self.visit(node.right, parent=node)

    visit_Add = _binary_op
    visit_Sub = _binary_op
    visit_Mul = _binary_op
    visit_Div = _binary_op
    visit_FloorDiv = _binary_op
    visit_Pow = _binary_op
    visit_Mod = _binary_op
    visit_And = _binary_op
    visit_Or = _binary_op

    def _unary_op(self, node: nodes.UnaryExpr, parent: nodes.Node) -> None:
        """Visit an ``UnaryExpr`` (one node with one op) in the stream."""
        self.tokens.seek(j2tokens.operators[node.operator])
        self.visit(node.node, parent=node)

    visit_Pos = _unary_op
    visit_Neg = _unary_op

    def visit_Not(self, node: nodes.Not, parent: nodes.Node) -> None:
        """Visit a negated expression in the stream."""
        if isinstance(node.node, nodes.Test):
            return self.visit_Test(node.node, parent=node, negate=True)
        else:  # _unary_op with a name token
            self.tokens.seek(j2tokens.TOKEN_NAME, node.operator)
            return self.visit(node.node, parent=node)

    def visit_Concat(self, node: nodes.Concat, parent: nodes.Node) -> None:
        """Visit a string concatenation expression in the stream.

        The Concat operator ``~`` concatenates expressions
        after converting them to strings.
        """
        for idx, expr in enumerate(node.nodes):
            if idx:
                self.tokens.seek(j2tokens.TOKEN_TILDE)
            self.visit(expr, parent=node)

    def visit_Compare(self, node: nodes.Compare, parent: nodes.Node) -> None:
        """Visit a ``Compare`` operator in the stream."""
        self.visit(node.expr, parent=node)

        # spell-checker:disable
        for operand in node.ops:
            # node.ops: List[Operand]
            # op.op: eq, ne, gt, gteq, lt, lteq, in, notin
            self.visit(operand, parent=node)
        # spell-checker:enable

    def visit_Operand(self, node: nodes.Operand, parent: nodes.Node) -> None:
        """Visit an ``Operand`` in the stream."""
        self.tokens.seek(operands[node.op])
        self.visit(node.expr, parent=node)

    def visit_Getattr(self, node: nodes.Getattr, parent: nodes.Node) -> None:
        """Visit a ``Getattr`` expression in the stream."""
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node, parent=node)
        self.tokens.seek(j2tokens.TOKEN_DOT)
        self.tokens.seek(j2tokens.TOKEN_NAME, node.attr)

    def visit_Getitem(self, node: nodes.Getitem, parent: nodes.Node) -> None:
        """Visit a ``Getitem`` expression in the stream."""
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node, parent=node)
        with self.token_pair_expression(node, j2tokens.TOKEN_LBRACKET):
            self.visit(node.arg, parent=node)

    def visit_Slice(self, node: nodes.Slice, parent: nodes.Node) -> None:
        """Visit a ``Slice`` expression in the stream."""
        if node.start is not None:
            self.visit(node.start, parent=node)
        self.tokens.seek(j2tokens.TOKEN_COLON)
        if node.stop is not None:
            self.visit(node.stop, parent=node)
        if node.step is not None:
            self.tokens.seek(j2tokens.TOKEN_COLON)
            self.visit(node.step, parent=node)

    def visit_Filter(self, node: nodes.Filter, parent: nodes.Node) -> None:
        """Visit a Jinja ``Filter`` in the stream."""
        if node.node is not None:
            self.visit(node.node, parent=node)
            self.tokens.seek(j2tokens.TOKEN_PIPE)
        self.tokens.seek(j2tokens.TOKEN_NAME, node.name)
        if any((node.args, node.kwargs, node.dyn_args, node.dyn_kwargs)):
            self.signature(node)

    def visit_Test(
        self, node: nodes.Test, parent: nodes.Node, negate: bool = False
    ) -> None:
        """Visit a Jinja ``Test`` in the stream."""
        self.visit(node.node, parent=node)
        names = ["is"]
        if negate:
            names.append("not")
        names.append(node.name)
        self.seek_past(j2tokens.TOKEN_NAME, *names)
        if any((node.args, node.kwargs, node.dyn_args, node.dyn_kwargs)):
            self.signature(node)

    def visit_CondExpr(self, node: nodes.CondExpr, parent: nodes.Node) -> None:
        """Visit a conditional expression in the stream.

        A conditional expression (inline ``if`` expression)::

            {{ foo if bar else baz }}
        """
        self.visit(node.expr1, parent=node)
        self.tokens.seek(j2tokens.TOKEN_NAME, "if")
        self.visit(node.test, parent=node)
        if node.expr2 is not None:
            self.tokens.seek(j2tokens.TOKEN_NAME, "else")
            self.visit(node.expr2, parent=node)

    def visit_Call(self, node: nodes.Call, parent: nodes.Node) -> None:
        """Visit a function ``Call`` expression in the stream."""
        self.visit(node.node, parent=node)
        self.signature(node)

    def visit_Keyword(self, node: nodes.Keyword, parent: nodes.Node) -> None:
        """Visit a dict ``Keyword`` expression in the stream."""
        self.tokens.seek(j2tokens.TOKEN_NAME, node.key)
        self.tokens.seek(j2tokens.TOKEN_ASSIGN)
        self.visit(node.value, parent=node)

    # -- Unused nodes for extensions

    # def visit_MarkSafe(self, node: nodes.MarkSafe, parent: nodes.Node) -> None:
    #     """ast node added by extensions, could dump to template if syntax were known"""

    # def visit_MarkSafeIfAutoescape(self, node: nodes.MarkSafeIfAutoescape, parent: nodes.Node) -> None:
    #     """Used by InternationalizationExtension"""
    #     # i18n adds blocks: ``trans/pluralize/endtrans``, but they are not in ast

    # def visit_EnvironmentAttribute(self, node: nodes.EnvironmentAttribute, parent: nodes.Node) -> None:
    #     """ast node added by extensions, not present in orig template"""

    # def visit_ExtensionAttribute(self, node: nodes.ExtensionAttribute, parent: nodes.Node) -> None:
    #     """ast node added by extensions, not present in orig template"""

    # def visit_ImportedName(self, node: nodes.ImportedName, parent: nodes.Node) -> None:
    #     """ast node added by extensions, could dump to template if syntax were known"""

    # def visit_InternalName(self, node: nodes.InternalName, parent: nodes.Node) -> None:
    #     """ast node added by parser.free_identifier, not present in template"""

    # def visit_ContextReference(self, node: nodes.ContextReference, parent: nodes.Node) -> None:
    #     """Added by DebugExtension"""
    #     # triggered by debug block, but debug block is not present in ast

    # def visit_DerivedContextReference(self, node: nodes.DerivedContextReference, parent: nodes.Node) -> None:
    #     """could be added by extensions. like debug block but w/ locals"""

    # noinspection PyUnusedLocal
    def visit_Continue(
        self,
        node: nodes.Continue,
        parent: nodes.Node,  # pylint: disable=unused-argument
    ) -> None:
        """Visit a ``Continue`` block for the LoopControlExtension in the stream."""
        with self.token_pair_block(node, "continue") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    # noinspection PyUnusedLocal
    def visit_Break(
        self, node: nodes.Break, parent: nodes.Node
    ) -> None:  # pylint: disable=unused-argument
        """Visit a ``Break`` block for the LoopControlExtension in the stream."""
        with self.token_pair_block(node, "break") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass

    # def visit_Scope(self, node: nodes.Scope, parent: nodes.Node) -> None:
    #     """could be added by extensions.
    #     Wraps the ScopedEvalContextModifier node for autoescape blocks
    #     """

    # def visit_OverlayScope(self, node: nodes.OverlayScope, parent: nodes.Node) -> None:
    #     """could be added by extensions."""

    # def visit_EvalContextModifier(self, node: nodes.EvalContextModifier, parent: nodes.Node) -> None:
    #     """could be added by extensions."""

    def visit_ScopedEvalContextModifier(
        self, node: nodes.ScopedEvalContextModifier, parent: nodes.Node
    ) -> None:
        """Visit an ``autoescape``/``endautoescape`` block in the stream."""
        autoescape = None
        for keyword_node in node.options:
            if keyword_node.key == "autoescape":
                autoescape = keyword_node.value
                break
        if autoescape is None:
            # unknown Modifier block
            self.generic_visit(node)
            return
        with self.token_pair_block(node, "autoescape") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            self.visit(autoescape, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endautoescape") as (
            pre_tokens,
            start_token,
            stop_token,
        ):
            pass
