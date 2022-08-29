"""Jinja AST tokens annotator."""
# pylint: disable=too-many-lines
from __future__ import annotations

from contextlib import contextmanager, nullcontext
from typing import Any, ContextManager, Iterator, List, cast

from jinja2 import lexer as j2tokens
from jinja2 import nodes
from jinja2.environment import Environment
from jinja2.visitor import NodeVisitor

from .token import BEGIN_TOKENS, END_TOKENS, Token, Tokens, pre_iter_normalize_newlines


# pylint: disable=too-few-public-methods
class _AnnotatedNode:
    """Our custom Jinja AST annotations."""

    tokens: tuple[int, int]
    parent: nodes.Node


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
        if not values:
            values = [None]  # type: ignore
        for value in values:
            self.tokens.seek(token_type, value)

    def find_lparen(
        self, start_index: int, end_index: int
    ) -> tuple[bool, Token | None]:
        """Find a left parentheses token in the range of token indexes."""
        found_lparen = False
        for token in self.tokens[start_index:end_index]:
            found_lparen = token.token == j2tokens.TOKEN_LPAREN or (
                token.jinja_token is not None
                and token.jinja_token.type == j2tokens.TOKEN_LPAREN
            )
            if found_lparen:
                return found_lparen, token
        return found_lparen, None

    def find_containing_pair_start(self, index: int) -> int:
        """Find the index to the nearest parent pair of tokens.

        Most tokens are contained in some pair of tokens such as ``{{ }}`` or ``( )``.
        This searches from a given token through earlier tokens until such a pair is
        found, or until no tokens are left.
        """
        while index > 0:
            token = self.tokens[index]
            if token.pair is not None:
                if token.token in END_TOKENS:
                    index = token.pair.index - 1
                    continue
                if token.token in BEGIN_TOKENS:
                    return token.index
            index -= 1
        return 0

    # -- Annotation Helpers

    def annotate(
        self,
        node: nodes.Node,
        *,
        start: int,
        end: int,
        parent: nodes.Node | None = None,
    ) -> None:
        """Annotate Jinja2 AST Node with token details."""
        cast(_AnnotatedNode, node).tokens = (start, end)
        if parent is not None:
            cast(_AnnotatedNode, node).parent = parent

    @staticmethod
    def get_chomp_index(pre_tokens: list[Token]) -> int:
        """Find the index of the last non-whitespace token in the given tokens."""
        whitespace_tokens = []
        for token in reversed(pre_tokens):
            if token.jinja_token is None:
                whitespace_tokens.append(token)
            else:
                break
        return whitespace_tokens[-1].index

    @contextmanager
    def token_pair_block(
        self, node: nodes.Node, *names: str, parent: nodes.Node | None = None
    ) -> Iterator[None]:
        """Find block tokens ``{% %}``, yield, and then annotate the node."""
        pre_tokens, start_token = self.tokens.seek(j2tokens.TOKEN_BLOCK_BEGIN)
        if start_token is None:
            raise IndexError("Could not find the {% token!")

        # bypass each of the block's names
        self.seek_past(j2tokens.TOKEN_NAME, *names)
        stop_token = cast(Token, start_token.pair)  # assume there is a matching %}
        if hasattr(node, "tokens"):
            # some nodes consist of multiple blocks. In that case, just extend the end.
            start_index = cast(_AnnotatedNode, node).tokens[0]
        elif start_token.chomp and pre_tokens:
            start_index = self.get_chomp_index(pre_tokens)
        else:
            start_index = start_token.index

        yield

        stop_index = stop_token.index
        self.tokens.index = stop_index + 1
        self.annotate(node, start=start_index, end=stop_index + 1, parent=parent)

    @contextmanager
    def token_pair_variable(
        self, node: nodes.Node, parent: nodes.Node | None = None
    ) -> Iterator[None]:
        """Find variable tokens ``{{ }}``, yield, and then annotate the node."""
        pre_tokens, start_token = self.tokens.seek(j2tokens.TOKEN_VARIABLE_BEGIN)
        if start_token is None:
            raise IndexError("Could not find the {{ token!")

        stop_token = cast(Token, start_token.pair)  # assume there is a matching %}
        if start_token.chomp and pre_tokens:
            start_index = self.get_chomp_index(pre_tokens)
        else:
            start_index = start_token.index

        yield

        stop_index = stop_token.index
        assert (
            self.tokens.index <= stop_index
        )  # how could child nodes pass the end token?!
        self.tokens.index = stop_index + 1
        self.annotate(node, start=start_index, end=stop_index + 1, parent=parent)

    @contextmanager
    def token_pair_expression(
        self, node: nodes.Node, left_token: str, parent: nodes.Node | None = None
    ) -> Iterator[None]:
        """Find paired tokens ``{}()[]``, yield, and then annotate the node."""
        _, start_token = self.tokens.seek(left_token)
        if start_token is None:
            raise IndexError(f"Could not find the {left_token} token!")

        stop_token = cast(Token, start_token.pair)  # assume there is a matching %}
        if hasattr(node, "tokens"):
            # some nodes consist of multiple blocks. In that case, just extend the end.
            start_index = cast(_AnnotatedNode, node).tokens[0]
        else:
            start_index = start_token.index

        yield

        stop_index = stop_token.index
        assert (
            self.tokens.index <= stop_index
        )  # how could child nodes pass the end token?!
        self.tokens.index = stop_index + 1
        self.annotate(node, start=start_index, end=stop_index + 1, parent=parent)

    # -- Various compilation helpers

    def signature(
        self,
        node: nodes.Call | nodes.Filter | nodes.Test,
    ) -> None:
        """Write a function call to the stream for the current node."""
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
        node: nodes.Macro | nodes.CallBlock,
        parent: nodes.Node | None = None,
    ) -> None:
        """Write a Macro or CallBlock signature to the stream for the current node."""
        with self.token_pair_expression(node, j2tokens.TOKEN_LPAREN, parent=parent):
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
        _, eof_token = self.tokens.seek(j2tokens.TOKEN_EOF)
        if eof_token is None:
            raise IndexError("Could not find the EOF token!")

        assert self.tokens.end
        self.annotate(node, start=initial_token.start_pos, end=eof_token.end_pos)

    def generic_visit(self, node: nodes.Node, *args: Any, **kwargs: Any) -> Any:
        """Visit a generic ``Node``.

        Called if no explicit visitor function exists for a node.
        """
        for child_node in node.iter_child_nodes():
            kwargs["parent"] = node
            self.visit(child_node, *args, **kwargs)

    def visit_Output(self, node: nodes.Output, parent: nodes.Node) -> None:
        """Visit an ``Output`` node in the stream.

        Output is a ``{{ }}`` statement (aka ``print`` or output statement).
        """
        for child_node in node.iter_child_nodes():
            # child_node.parent = node
            # child_node might be TemplateData which is outside {{ }}
            if isinstance(child_node, nodes.TemplateData):
                self.visit(child_node, parent=node)
                continue

            # NOTE: this does not handle extension-injected nodes yet

            # child_node is one of the expression nodes surrounded by {{ }}
            with self.token_pair_variable(child_node, parent=node):
                self.visit(child_node, parent=node)

        self.annotate(
            node,
            start=cast(_AnnotatedNode, node.nodes[0]).tokens[0],
            end=cast(_AnnotatedNode, node.nodes[-1]).tokens[1] + 1,
            parent=parent,
        )

    def visit_Block(self, node: nodes.Block, parent: nodes.Node) -> None:
        """Visit a ``Block`` in the stream.

        Examples::

            {% block name %}block{% endblock %}
            {% block name scoped %}block{% endblock %}
            {% block name scoped required %}block{% endblock %}
            {% block name required %}block{% endblock %}
        """
        block_name_tokens: list[str] = ["block", node.name]
        # jinja parser only supports one order: scoped required
        if node.scoped:
            block_name_tokens.append("scoped")
        if node.required:
            block_name_tokens.append("required")
        with self.token_pair_block(node, *block_name_tokens, parent=parent):
            pass
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endblock", parent=parent):
            pass

    def visit_Extends(self, node: nodes.Extends, parent: nodes.Node) -> None:
        """Visit an ``Extends`` block in the stream.

        Example::

            {% extends name %}
        """
        with self.token_pair_block(node, "extends", parent=parent):
            self.visit(node.template, parent=node)

    def visit_Include(self, node: nodes.Include, parent: nodes.Node) -> None:
        """Visit an ``Include`` block in the stream.

        Examples::

            {% include name %}
            {% include name ignore missing %}
            {% include name ignore missing without context %}
            {% include name without context %}
        """
        with self.token_pair_block(node, "include", parent=parent):
            self.visit(node.template, parent=node)
            if node.ignore_missing:
                self.seek_past(j2tokens.TOKEN_NAME, "ignore", "missing")
            # include defaults to "with context"
            if not node.with_context:
                self.seek_past(j2tokens.TOKEN_NAME, "without", "context")
            # with context (implicit default) may be explicitly specified
            # but will be skipped via the block pair.

    def visit_Import(self, node: nodes.Import, parent: nodes.Node) -> None:
        """Visit an ``Import`` block in the stream.

        Examples::

            {% import expr as name %}
            {% import expr as name without context %}
        """
        with self.token_pair_block(node, "import", parent=parent):
            self.visit(node.template, parent=node)
            self.seek_past(j2tokens.TOKEN_NAME, "as", node.target)
            # import defaults to "without context"
            if node.with_context:
                self.seek_past(j2tokens.TOKEN_NAME, "with", "context")
            # without context (implicit default) may be explicitly specified
            # but will be skipped via the block pair.

    def visit_FromImport(self, node: nodes.FromImport, parent: nodes.Node) -> None:
        """Visit a ``FromImport`` block in the stream.

        Examples::

            {% from expr import expr as name %}
            {% from expr import expr as name without context %}
        """
        with self.token_pair_block(node, "from", parent=parent):
            self.visit(node.template, parent=node)
            self.tokens.seek(j2tokens.TOKEN_NAME, "import")
            for idx, name in enumerate(node.names):
                if idx:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                if isinstance(name, tuple):
                    self.seek_past(j2tokens.TOKEN_NAME, name[0], "as", name[1])
                else:  # str
                    self.tokens.seek(j2tokens.TOKEN_NAME, name)
                # final comma is also optional and gets skipped with block pair
            if node.with_context:
                self.seek_past(j2tokens.TOKEN_NAME, "with", "context")
            # without context (implicit default) may be explicitly specified
            # but will be skipped via the block pair.

    def visit_For(self, node: nodes.For, parent: nodes.Node) -> None:
        """Visit a ``For`` block in the stream.

        Examples::

            {% for target in iter %}block{% endfor %}
            {% for target in iter recursive %}block{% endfor %}
            {% for target in iter %}block{% else %}block{% endfor %}
        """
        with self.token_pair_block(node, "for", parent=parent):
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
            with self.token_pair_block(node, "else", parent=parent):
                pass
            for child_node in node.else_:
                self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endfor", parent=parent):
            pass

    def visit_If(self, node: nodes.If, parent: nodes.Node) -> None:
        """Visit an ``If`` block in the stream."""
        with self.token_pair_block(node, "if", parent=parent):
            self.visit(node.test, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        for elif_node in node.elif_:
            self.visit_Elif(elif_node, parent=node)
        if node.else_:
            with self.token_pair_block(node, "else", parent=parent):
                pass
            for child_node in node.else_:
                self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endif", parent=parent):
            pass

    def visit_Elif(self, node: nodes.If, parent: nodes.Node) -> None:
        """Visit an ``If`` block that serves as an elif node in another ``If`` block."""
        with self.token_pair_block(node, "elif", parent=parent):
            self.visit(node.test, parent=node)
        start_index, stop_index = cast(_AnnotatedNode, node).tokens
        for child_node in node.body:
            self.visit(child_node, parent=node)
            stop_index = cast(_AnnotatedNode, child_node).tokens[1]
        self.annotate(node, start=start_index, end=stop_index, parent=parent)

    def visit_With(self, node: nodes.With, parent: nodes.Node) -> None:
        """Visit a ``With`` statement (manual scopes) in the stream."""
        with self.token_pair_block(node, "with", parent=parent):
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
        with self.token_pair_block(node, "endwith", parent=parent):
            pass

    def visit_ExprStmt(self, node: nodes.ExprStmt, parent: nodes.Node) -> None:
        """Visit a ``do`` block in the stream.

        ExprStmtExtension
            A ``do`` tag is like a ``print`` statement but doesn't print the return value.
        ExprStmt
            A statement that evaluates an expression and discards the result.
        """
        with self.token_pair_block(node, "do", parent=parent):
            self.visit(node.node, parent=node)

    def visit_Assign(self, node: nodes.Assign, parent: nodes.Node) -> None:
        """Visit an ``Assign`` statement in the stream.

        Example::

            {% set var = value %}
        """
        with self.token_pair_block(node, "set", parent=parent):
            self.visit(node.target, parent=node)
            self.tokens.seek(j2tokens.TOKEN_ASSIGN)
            self.visit(node.node, parent=node)

    # noinspection DuplicatedCode
    def visit_AssignBlock(self, node: nodes.AssignBlock, parent: nodes.Node) -> None:
        """Visit an ``Assign`` block in the stream.

        Example::

            {% set var %}value{% endset %}
        """
        with self.token_pair_block(node, "set", parent=parent):
            self.visit(node.target, parent=node)
            if node.filter is not None:
                self.visit(node.filter, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endset", parent=parent):
            pass

    # noinspection DuplicatedCode
    def visit_FilterBlock(self, node: nodes.FilterBlock, parent: nodes.Node) -> None:
        """Visit a ``Filter`` block in the stream.

        Example::

            {% filter <filter> %}block{% endfilter %}
        """
        with self.token_pair_block(node, "filter", parent=parent):
            self.visit(node.filter, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endfilter", parent=parent):
            pass

    def visit_Macro(self, node: nodes.Macro, parent: nodes.Node) -> None:
        """Visit a ``Macro`` definition block in the stream.

        Example::

            {% macro name(args/defaults) %}block{% endmacro %}
        """
        with self.token_pair_block(node, "macro", node.name, parent=parent):
            self.macro_signature(node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endmacro", parent=parent):
            pass

    def visit_CallBlock(self, node: nodes.CallBlock, parent: nodes.Node) -> None:
        """Visit a macro ``Call`` block in the stream.

        Examples::

            {% call macro() %}block{% endcall %}
            {% call(args/defaults) macro() %}block{% endcall %}
        """
        with self.token_pair_block(node, "call", parent=parent):
            if node.args:
                self.macro_signature(node)
            self.visit(node.call, parent=node)
        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endcall", parent=parent):
            pass

    # -- Expression Visitors

    def visit_Name(self, node: nodes.Name, parent: nodes.Node) -> None:
        """Visit a ``Name`` expression in the stream."""
        # ctx is one of: load, store, param
        # load named var, store named var, or store named function parameter
        _, token = self.tokens.seek(j2tokens.TOKEN_NAME, node.name)
        if token is None:
            raise IndexError(f"Could not find {node.name} name token!")
        self.annotate(node, start=token.index, end=token.index + 1, parent=parent)

    def visit_NSRef(self, node: nodes.NSRef, parent: nodes.Node) -> None:
        """Visit a ref to namespace value assignment in the stream."""
        _, token = self.tokens.seek(j2tokens.TOKEN_NAME, node.name)
        if token is None:
            raise IndexError(f"Could not find {node.name} name token!")
        start_index = token.index
        self.tokens.seek(j2tokens.TOKEN_DOT)
        _, token = self.tokens.seek(j2tokens.TOKEN_NAME, node.attr)
        if token is None:
            raise IndexError(f"Could not find {node.attr} name token!")
        stop_index = token.index
        self.annotate(node, start=start_index, end=stop_index + 1, parent=parent)

    def visit_Const(self, node: nodes.Const, parent: nodes.Node) -> None:  # Literal
        """Visit a Literal constant value (``int``, ``str``, etc) in the stream."""
        # We are using repr() here to handle quoting strings.
        if node.value is None or isinstance(node.value, bool):
            _, token = self.tokens.seek(j2tokens.TOKEN_NAME)
            if token is None:
                raise IndexError(f"Could not find {node.value} name token!")
            start_index, stop_index = token.index, token.index
        elif isinstance(node.value, int):
            _, token = self.tokens.seek(j2tokens.TOKEN_INTEGER)
            if token is None:
                raise IndexError(f"Could not find {node.value} integer token!")
            start_index, stop_index = token.index, token.index
        elif isinstance(node.value, float):
            _, token = self.tokens.seek(j2tokens.TOKEN_FLOAT)
            if token is None:
                raise IndexError(f"Could not find {node.value} float token!")
            start_index, stop_index = token.index, token.index
        elif isinstance(node.value, str):
            # string consumes multiple tokens
            _, token = self.tokens.seek(j2tokens.TOKEN_STRING)
            if token is None:
                raise IndexError(f"Could not find {repr(node.value)} string token(s)!")
            start_index, stop_index = token.index, token.index
            token = self.tokens.current
            while token.jinja_token is None or token.token == j2tokens.TOKEN_STRING:
                stop_index = token.index
                token = next(self.tokens)
        else:
            raise ValueError(
                f"Const node.value has unexpected type: {type(node.value)}"
            )
        self.annotate(node, start=start_index, end=stop_index + 1, parent=parent)

    def visit_TemplateData(self, node: nodes.TemplateData, parent: nodes.Node) -> None:
        """Visit a Literal constant string (between Jinja blocks)."""
        _, token = self.tokens.seek(j2tokens.TOKEN_DATA, node.data)
        if token is None:
            raise IndexError(f"Could not find {repr(node.data)} data token!")
        self.annotate(node, start=token.index, end=token.index + 1, parent=parent)

    def visit_Tuple(self, node: nodes.Tuple, parent: nodes.Node) -> None:
        """Visit a Literal ``Tuple`` in the stream."""
        if not node.items:
            # empty tuple
            with self.token_pair_expression(node, j2tokens.TOKEN_LPAREN, parent=parent):
                pass
            return

        # spell-checker: disable
        # parentheses are optional in many contexts
        # parser creates tuples in these contexts+options:
        #   parse_primary (const, etc)
        #      -> explicit_parentheses=True
        #      -> with_condexpr=True
        #   variable {{ }} -> with_condexpr=True
        #   assign <target> = <expr> ->
        #      target -> simplified=True || parse_primary
        #      expr -> with_condexpr=True
        #   for <target> in <expr>
        #      target -> simplified=True
        #      expr -> with_condexpr=False
        #   if <test>
        #      test -> with_condexpr=False
        # spell-checker: enable
        initial_index = self.tokens.index

        # pass first item and any lparen
        self.visit(node.items[0], parent=node)
        item_index, after_index = cast(_AnnotatedNode, node.items[0]).tokens
        start_index = item_index

        found_lparen, lparen_token = self.find_lparen(
            start_index=initial_index, end_index=item_index
        )

        pair_wrapper: Iterator[None] | ContextManager[None]
        if found_lparen:
            # reset tokens back to lparen token
            self.tokens.index = start_index = cast(Token, lparen_token).index
            pair_wrapper = self.token_pair_expression(
                node, j2tokens.TOKEN_LPAREN, parent=parent
            )
        else:
            pair_wrapper = nullcontext()

        with pair_wrapper:
            for idx, item in enumerate(node.items):
                if idx == 0:
                    # already visited the first item above
                    self.tokens.index = after_index
                    continue
                self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(item, parent=node)
        # optional final comma gets skipped if parentheses pair is explicit
        if not found_lparen:
            # we need to check for the final comma in implicit tuple (w/o parentheses)
            after_index = cast(_AnnotatedNode, node.items[-1]).tokens[1]
            tokens = []
            for token in self.tokens[after_index:]:
                if token.jinja_token is None:
                    tokens.append(token)
                    continue
                tokens.append(token)
                break
            if tokens:
                token = tokens[-1]
                if (
                    token.jinja_token is not None
                    and token.jinja_token.type == j2tokens.TOKEN_COMMA
                ):
                    self.tokens.index = token.index + 1
                else:
                    self.tokens.index = after_index
            self.annotate(node, start=start_index, end=self.tokens.index, parent=parent)

    def visit_List(self, node: nodes.List, parent: nodes.Node) -> None:
        """Visit a Literal ``List`` in the stream."""
        with self.token_pair_expression(node, j2tokens.TOKEN_LBRACKET, parent=parent):
            for idx, item in enumerate(node.items):
                if idx:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(item, parent=node)
        # final comma is optional and gets skipped with brackets pair

    def visit_Dict(self, node: nodes.Dict, parent: nodes.Node) -> None:
        """Visit a Literal ``Dict`` in the stream."""
        with self.token_pair_expression(node, j2tokens.TOKEN_LBRACE, parent=parent):
            pair: nodes.Pair
            for idx, pair in enumerate(node.items):
                if idx:
                    self.tokens.seek(j2tokens.TOKEN_COMMA)
                self.visit(pair, parent=node)
        # final comma is optional and gets skipped with braces pair

    def visit_Pair(self, node: nodes.Pair, parent: nodes.Node) -> None:
        """Visit a Key/Value ``Pair`` in a Dict."""
        self.visit(node.key, parent=node)
        self.tokens.seek(j2tokens.TOKEN_COLON)
        self.visit(node.value, parent=node)
        self.annotate(
            node,
            start=cast(_AnnotatedNode, node.key).tokens[0],
            end=cast(_AnnotatedNode, node.value).tokens[1],
            parent=parent,
        )

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
        self.annotate(
            node,
            start=cast(_AnnotatedNode, node.left).tokens[0],
            end=cast(_AnnotatedNode, node.right).tokens[1],
            parent=parent,
        )

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
        _, token = self.tokens.seek(j2tokens.operators[node.operator])
        if token is None:
            raise IndexError(f"Could not find {node.operator} operator token!")
        self.visit(node.node, parent=node)
        self.annotate(
            node,
            start=token.index,
            end=cast(_AnnotatedNode, node.node).tokens[1],
            parent=parent,
        )

    visit_Pos = _unary_op
    visit_Neg = _unary_op

    def visit_Not(self, node: nodes.Not, parent: nodes.Node) -> None:
        """Visit a negated expression in the stream."""
        if isinstance(node.node, nodes.Test):
            self.visit_Test(node.node, parent=node, negate=True)
            self.annotate(
                node,
                start=cast(_AnnotatedNode, node.node).tokens[0],
                end=cast(_AnnotatedNode, node.node).tokens[1],
                parent=parent,
            )
        else:  # _unary_op with a name token
            _, token = self.tokens.seek(j2tokens.TOKEN_NAME, node.operator)
            if token is None:
                raise IndexError(f"Could not find {node.operator} name token!")
            self.visit(node.node, parent=node)
            self.annotate(
                node,
                start=token.index,
                end=cast(_AnnotatedNode, node.node).tokens[1],
                parent=parent,
            )

    def visit_Concat(self, node: nodes.Concat, parent: nodes.Node) -> None:
        """Visit a string concatenation expression in the stream.

        The Concat operator ``~`` concatenates expressions
        after converting them to strings.
        """
        for idx, expr in enumerate(node.nodes):
            if idx:
                self.tokens.seek(j2tokens.TOKEN_TILDE)
            self.visit(expr, parent=node)
        self.annotate(
            node,
            start=cast(_AnnotatedNode, node.nodes[0]).tokens[0],
            end=cast(_AnnotatedNode, node.nodes[-1]).tokens[1],
            parent=parent,
        )

    def visit_Compare(self, node: nodes.Compare, parent: nodes.Node) -> None:
        """Visit a ``Compare`` operator in the stream."""
        self.visit(node.expr, parent=node)

        # spell-checker: disable
        for operand in node.ops:
            # node.ops: List[Operand]
            # op.op: eq, ne, gt, gteq, lt, lteq, in, notin
            self.visit(operand, parent=node)
        # spell-checker: enable

        self.annotate(
            node,
            start=cast(_AnnotatedNode, node.expr).tokens[0],
            end=cast(_AnnotatedNode, node.ops[-1]).tokens[1],
            parent=parent,
        )

    def visit_Operand(self, node: nodes.Operand, parent: nodes.Node) -> None:
        """Visit an ``Operand`` in the stream."""
        if node.op == "in":
            _, token = self.tokens.seek(j2tokens.TOKEN_NAME, node.op)
            if token is None:
                raise IndexError("Could not find 'in' name token!")
        elif node.op == "notin":  # cspell:ignore notin
            _, token = self.tokens.seek(j2tokens.TOKEN_NAME, "not")
            if token is None:
                raise IndexError("Could not find 'not in' name tokens!")
            self.tokens.seek(j2tokens.TOKEN_NAME, "in")
        else:
            _, token = self.tokens.seek(node.op)
            if token is None:
                raise IndexError(f"Could not find {node.op} name token!")
        self.visit(node.expr, parent=node)
        self.annotate(
            node,
            start=token.index,
            end=cast(_AnnotatedNode, node.expr).tokens[1],
            parent=parent,
        )

    def visit_Getattr(self, node: nodes.Getattr, parent: nodes.Node) -> None:
        """Visit a ``Getattr`` expression in the stream."""
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node, parent=node)
        self.tokens.seek(j2tokens.TOKEN_DOT)
        _, token = self.tokens.seek(j2tokens.TOKEN_NAME, node.attr)
        if token is None:
            raise IndexError(f"Could not find {node.attr} name token!")
        self.annotate(
            node,
            start=cast(_AnnotatedNode, node.node).tokens[0],
            end=token.index + 1,
            parent=parent,
        )

    def visit_Getitem(self, node: nodes.Getitem, parent: nodes.Node) -> None:
        """Visit a ``Getitem`` expression in the stream."""
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node, parent=node)
        start_index, after_index = cast(_AnnotatedNode, node.node).tokens

        # Getitem can use [] or . notation, so look for a dot
        tokens = []
        for token in self.tokens[after_index:]:
            if token.jinja_token is None:
                tokens.append(token)
                continue
            tokens.append(token)
            break

        last_token: Token = tokens[-1]
        assert last_token.jinja_token is not None

        if last_token.jinja_token.type == j2tokens.TOKEN_DOT:
            # <node>.<arg> notation
            self.tokens.seek(j2tokens.TOKEN_DOT)
            self.visit(node.arg, parent=node)
            end_index = cast(_AnnotatedNode, node.arg).tokens[1]
        else:
            # <node>[<arg>] notation
            with self.token_pair_expression(
                node, j2tokens.TOKEN_LBRACKET, parent=parent
            ):
                self.visit(node.arg, parent=node)
            end_index = cast(_AnnotatedNode, node).tokens[1]
        self.annotate(node, start=start_index, end=end_index, parent=parent)

    def visit_Slice(self, node: nodes.Slice, parent: nodes.Node) -> None:
        """Visit a ``Slice`` expression in the stream."""
        start_index = end_index = None
        if node.start is not None:
            self.visit(node.start, parent=node)
            start_index = cast(_AnnotatedNode, node.start).tokens[0]
            end_index = cast(_AnnotatedNode, node.start).tokens[1]
        _, token = self.tokens.seek(j2tokens.TOKEN_COLON)
        if token is None:
            raise IndexError("Could not find ':' colon token!")
        if start_index is None:
            start_index = token.index
            end_index = token.index + 1
        if node.stop is not None:
            self.visit(node.stop, parent=node)
            end_index = cast(_AnnotatedNode, node.stop).tokens[1]
        if node.step is not None:
            self.tokens.seek(j2tokens.TOKEN_COLON)
            self.visit(node.step, parent=node)
            end_index = cast(_AnnotatedNode, node.step).tokens[1]
        self.annotate(node, start=start_index, end=cast(int, end_index), parent=parent)

    def visit_Filter(self, node: nodes.Filter, parent: nodes.Node) -> None:
        """Visit a Jinja ``Filter`` in the stream."""
        start_index = None
        # node.node can be None in an AssignBlock or FilterBlock
        if node.node is not None:
            self.visit(node.node, parent=node)
            _, token = self.tokens.seek(j2tokens.TOKEN_PIPE)
            start_index = cast(_AnnotatedNode, node.node).tokens[0]
        pre_tokens, token = self.tokens.seek(j2tokens.TOKEN_NAME, node.name)
        if token is None:
            raise IndexError(f"Could not find {node.name} name token!")
        if start_index is None:
            pipe_tokens = [
                t
                for t in pre_tokens
                if t.jinja_token is not None
                and t.jinja_token.type == j2tokens.TOKEN_PIPE
            ]
            if pipe_tokens:
                # AssignBlock needs the "|"
                start_index = pipe_tokens[-1].index
            else:
                # FilterBlock has an implicit "|"
                start_index = token.index
        end_index = token.index + 1
        if any((node.args, node.kwargs, node.dyn_args, node.dyn_kwargs)):
            with self.token_pair_expression(node, j2tokens.TOKEN_LPAREN, parent=parent):
                self.signature(node)
        if hasattr(node, "tokens"):
            end_index = cast(_AnnotatedNode, node).tokens[1]
        self.annotate(node, start=start_index, end=end_index, parent=parent)

    def visit_Test(
        self, node: nodes.Test, parent: nodes.Node, negate: bool = False
    ) -> None:
        """Visit a Jinja ``Test`` in the stream."""
        self.visit(node.node, parent=node)
        start_index = cast(_AnnotatedNode, node.node).tokens[0]
        names = ["is"]
        if negate:
            names.append("not")
        names.append(node.name)
        self.seek_past(j2tokens.TOKEN_NAME, *names)
        end_index = self.tokens.index
        if any((node.args, node.kwargs, node.dyn_args, node.dyn_kwargs)):
            pair_start_index = self.find_containing_pair_start(end_index)
            pair_end_index = cast(Token, self.tokens[pair_start_index].pair).index
            found_lparen, _ = self.find_lparen(
                start_index=end_index, end_index=pair_end_index
            )

            pair_wrapper: Iterator[None] | ContextManager[None]
            if found_lparen:
                pair_wrapper = self.token_pair_expression(
                    node, j2tokens.TOKEN_LPAREN, parent=parent
                )
            else:
                pair_wrapper = nullcontext()
                end_index = None  # type: ignore

            with pair_wrapper:
                self.signature(node)
        if hasattr(node, "tokens"):
            end_index = cast(_AnnotatedNode, node).tokens[1]
        elif end_index is None:
            end_index = self.tokens.index
        self.annotate(node, start=start_index, end=end_index, parent=parent)

    def visit_CondExpr(self, node: nodes.CondExpr, parent: nodes.Node) -> None:
        """Visit a conditional expression in the stream.

        A conditional expression (inline ``if`` expression)::

            {{ foo if bar else baz }}
        """
        self.visit(node.expr1, parent=node)
        start_index = cast(_AnnotatedNode, node.expr1).tokens[0]
        self.tokens.seek(j2tokens.TOKEN_NAME, "if")
        self.visit(node.test, parent=node)
        end_index = cast(_AnnotatedNode, node.test).tokens[1]
        if node.expr2 is not None:
            self.tokens.seek(j2tokens.TOKEN_NAME, "else")
            self.visit(node.expr2, parent=node)
            end_index = cast(_AnnotatedNode, node.expr2).tokens[1]
        self.annotate(node, start=start_index, end=end_index, parent=parent)

    def visit_Call(self, node: nodes.Call, parent: nodes.Node) -> None:
        """Visit a function ``Call`` expression in the stream."""
        self.visit(node.node, parent=node)
        start_index = cast(_AnnotatedNode, node.node).tokens[0]
        with self.token_pair_expression(node, j2tokens.TOKEN_LPAREN, parent=parent):
            self.signature(node)
        end_index = cast(_AnnotatedNode, node).tokens[1]
        self.annotate(node, start=start_index, end=end_index, parent=parent)

    def visit_Keyword(self, node: nodes.Keyword, parent: nodes.Node) -> None:
        """Visit a dict ``Keyword`` expression in the stream."""
        _, token = self.tokens.seek(j2tokens.TOKEN_NAME, node.key)
        if token is None:
            raise IndexError(f"Could not find {node.key} name token!")
        self.tokens.seek(j2tokens.TOKEN_ASSIGN)
        self.visit(node.value, parent=node)
        self.annotate(
            node,
            start=token.index,
            end=cast(_AnnotatedNode, node.value).tokens[1],
            parent=parent,
        )

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
        with self.token_pair_block(node, "continue", parent=parent):
            pass

    # noinspection PyUnusedLocal
    def visit_Break(
        self, node: nodes.Break, parent: nodes.Node
    ) -> None:  # pylint: disable=unused-argument
        """Visit a ``Break`` block for the LoopControlExtension in the stream."""
        with self.token_pair_block(node, "break", parent=parent):
            pass

    def visit_Scope(self, node: nodes.Scope, parent: nodes.Node) -> None:
        """Visit a ``Scope`` node which can be added by extensions.

        Wraps the ScopedEvalContextModifier node for autoescape blocks
        """
        self.generic_visit(node)
        start_index = cast(_AnnotatedNode, node.body[0]).tokens[0]
        end_index = cast(_AnnotatedNode, node.body[-1]).tokens[1]
        self.annotate(node, start=start_index, end=end_index, parent=parent)

    # def visit_OverlayScope(self, node: nodes.OverlayScope, parent: nodes.Node) -> None:
    #     """could be added by extensions."""

    # def visit_EvalContextModifier(self, node: nodes.EvalContextModifier, parent: nodes.Node) -> None:
    #     """could be added by extensions."""

    def visit_ScopedEvalContextModifier(
        self, node: nodes.ScopedEvalContextModifier, parent: nodes.Node
    ) -> None:
        """Visit an ``autoescape``/``endautoescape`` block in the stream."""
        keyword_node = autoescape = None
        for keyword_node in node.options:
            if keyword_node.key == "autoescape":
                autoescape = keyword_node.value
                break
        if autoescape is None:
            # unknown Modifier block
            self.generic_visit(node)
            return
        with self.token_pair_block(node, "autoescape", parent=parent):
            self.visit(keyword_node.value, parent=keyword_node)

        start_index, end_index = cast(_AnnotatedNode, node).tokens
        for token in self.tokens[start_index:end_index]:
            if (
                token.token == j2tokens.TOKEN_NAME
                and token.jinja_token is not None
                and token.jinja_token.value == "autoescape"
            ):
                start_index = token.index
                break
        end_index = cast(_AnnotatedNode, keyword_node.value).tokens[1]
        self.annotate(keyword_node, start=start_index, end=end_index, parent=parent)

        for child_node in node.body:
            self.visit(child_node, parent=node)
        with self.token_pair_block(node, "endautoescape", parent=parent):
            pass
