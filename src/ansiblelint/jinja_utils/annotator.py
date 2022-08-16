"""Jinja AST whitespace annotator."""

from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from typing import List, Optional, TextIO, Tuple, Union, cast

from jinja2 import nodes
from jinja2.compiler import operators
from jinja2.environment import Environment
from jinja2.visitor import NodeVisitor


def annotate_whitespace(
    node: nodes.Template,
    environment: Environment,
    raw_template: str,
) -> nodes.Template:
    """Annotate a jinja2 AST with info about whitespace.

    This is based on jinja2.compiler.generate
    """
    if not isinstance(node, nodes.Template):
        raise TypeError("Can't dump non template nodes")

    annotator = WhitespaceAnnotator(environment, raw_template)
    annotator.visit(node)

    return node


@dataclass
class Whitespace:
    # indexes/positions of the full jinja template
    start: int
    end: int
    # list of whitespace index ranges (chars ignored by Jinja)
    # example: ((2, 4), (9, 10)) for {{  block }}
    ranges: Tuple[Tuple[int, int], ...]
    start_marker: Optional[int] = None  # first char of {{ or {%
    end_marker: Optional[int] = None  # first char of }} or %}

    # other important bits
    block: str = ""  # empty string if not block
    start_chomp: bool = False  # {{-, {%-
    end_chomp: bool = False  # -}}, -%}


# Ignore these because they're required by Jinja2's NodeVisitor interface
# pylint: disable=too-many-public-methods,invalid-name
class WhitespaceAnnotator(NodeVisitor):
    """Annotate a jinja2 AST with info about whitespace."""

    def __init__(
        self,
        environment: Environment,
        raw_template: str,
    ):
        """Create a TemplateDumper."""
        self.environment = environment
        self.stream = raw_template
        self._index = 0
        self._whitespace_ranges: List[Tuple[int, int], ...] = []

    # -- Seek Helpers

    def seek(needle: str) -> int:
        # assumption: we have the ast, so we should only seek
        # with strings that are known to be in the template.
        index = self.stream.index(needle, self._index)
        self._index = index + len(needle)
        return index

    def chomp() -> bool:
        """Move stream index to next non-whitespace char."""
        index = self._index
        chomped_index = next(
            i for i, char in enumerate(self.stream[index:], index) if char.strip()
        )
        self._index = chomped_index
        return index != chomped_index

    def chomp_to(ranges: List[Tuple[int, int], ...]):
        """Chomp whitespace and record in given ranges list."""
        index = self._index
        if self.chomp():
            ranges.append((index, self._index))

    # -- Annotation Helpers

    def annotate(
        self,
        node: nodes.Node,
        *,
        start: int,
        end: int,
        block: Optional[str] = None,
        start_marker: Optional[int] = None,
        start_chomp: bool = False,
        end_chomp: bool = False,
        end_marker: Optional[int] = None,
        whitespace_ranges: Tuple[Tuple[int, int], ...] = (),
    ) -> None:
        # some nodes have multiple block tags
        # so this has whitespace info for each tag
        whitespaces: List[Whitespace] = getattr(node, "whitespaces", [])
        whitespaces.append(
            Whitespace(
                start=start,
                end=end,
                block=block,
                start_marker=start_marker,
                start_chomp=start_chomp,
                end_chomp=end_chomp,
                end_marker=end_marker,
                ranges=whitespace_ranges,
            )
        )
        node.whitespaces = whitespaces

    def simple_seek_and_annotate(
        self,
        needle: str,
        node: nodes.Node,
    ) -> None:
        """Seek a simple needle and annoate node.

        This is for simple expression nodes that need only one seek.
        """
        start = self._index
        index = self.seek(needle)
        ranges = ((start, index),) if start != index else ()
        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=ranges)

    @contextmanager
    def annotate_marker(
        self,
        node: nodes.Node,
        block: Optional[str] = None,
    ) -> None:
        # comment {# #} is not available in the AST
        start_marker_string: str  # {{, {%
        end_marker_string: str  # }}, %}
        if block:
            start_marker_string = self.environment.block_start_string
            end_marker_string = self.environment.block_end_string
        else:
            start_marker_string = self.environment.variable_start_string
            end_marker_string = self.environment.variable_end_string

        # child nodes count as part of this block
        ranges = self._whitespace_ranges = []

        start = self._index
        start_marker = self.seek(start_marker_string)
        if start != start_marker:
            # This relies on the assumption that the previous AST node stopped
            # consuming the stream at the end of its content.
            # So, we should only get here if start_chomp
            # or there is whitespace at the beginning of tge line that jinja ignores.
            ranges.append((start, start_marker))

        # start_preserve_ws = self.stream[self._index] == "+"
        start_chomp = self.stream[self._index] == "-"
        if start_chomp:  # or start_preserve_ws:
            self._index += 1

        if block is not None:
            before_block = self._index
            index = self.seek(block)
            if before_block != index:
                ranges.append((before_block, index))
            self.chomp_to(ranges)

        # child nodes will use self._whitespace_ranges.append(...) to record whitespace
        yield
        self.chomp_to(ranges)

        end_marker = self.seek(end_marker_string)
        end_chomp = self.stream[end_marker - 1] == "-"
        # end_preserve_ws = self.stream[end_marker-1] == "+"
        if end_chomp:
            self.chomp_to(ranges)
        end = self._index

        self.annotate(
            child_node,
            start=start,
            end=end,
            block=block,
            start_marker=start_marker,  # first char of {%
            start_chomp=start_chomp,  # {%-
            end_chomp=end_chomp,  # -%}
            end_marker=end_marker,  # first char of %}
            whitespace_ranges=tuple(ranges),
        )

        # reset for the next AST node
        self._whitespace_ranges = []

    # -- Various compilation helpers

    def signature(
        self,
        node: Union[nodes.Call, nodes.Filter, nodes.Test],
    ) -> None:
        """Write a function call to the stream for the current node."""
        ranges = self._whitespace_ranges

        first = True
        arg: nodes.Expr
        for arg in node.args:
            if first:
                first = False
            else:
                self.seek(",")
                self.chomp_to(ranges)
            self.visit(arg)
            self.chomp_to(ranges)
        # cast because typehint is incorrect on nodes._FilterTestCommon
        for kwarg in cast(List[nodes.Keyword], node.kwargs):
            if first:
                first = False
            else:
                self.seek(",")
                self.chomp_to(ranges)
            self.visit(kwarg)
            self.chomp_to(ranges)
        if node.dyn_args:
            if first:
                first = False
            else:
                self.seek(",")
                self.chomp_to(ranges)
            self.seek("*")
            self.chomp_to(ranges)
            self.visit(node.dyn_args)
            self.chomp_to(ranges)
        if node.dyn_kwargs is not None:
            if first:
                first = False
            else:
                self.seek(",")
                self.chomp_to(ranges)
            self.seek("**")
            self.chomp_to(ranges)
            self.visit(node.dyn_kwargs)

    def macro_signature(
        self,
        node: Union[nodes.Macro, nodes.CallBlock],
    ) -> None:
        """Write a Macro or CallBlock signature to the stream for the current node."""
        ranges = self._whitespace_ranges

        self.seek("(")
        self.chomp_to(ranges)
        for idx, arg in enumerate(node.args):
            if idx:
                self.seek(",")
                self.chomp_to(ranges)
            self.visit(arg)
            try:
                default = node.defaults[idx - len(node.args)]
            except IndexError:
                continue
            self.chomp_to(ranges)
            self.seek("=")
            self.chomp_to(ranges)
            self.visit(default)
            self.chomp_to(ranges)
        self.seek(")")

    # -- Statement Visitors

    def visit_Template(self, node: nodes.Template) -> None:
        """Template is the root node."""
        ranges = []
        self.generic_visit(node)
        end = self._index
        end_of_stream = len(self.stream)
        if end != end_of_stream:
            ranges.append((end, end_of_stream))
        self.annotate(node, start=0, end=end_of_stream, ranges=tuple(ranges))

    def visit_Output(self, node: nodes.Template) -> None:
        """Visit an ``Output`` node in the stream.

        Output is a ``{{ }}`` statement (aka ``print`` or output statement).
        """
        start = self._index
        for child_node in node.iter_child_nodes():
            # child_node might be TemplateData which is outside {{ }}
            if isinstance(child_node, nodes.TemplateData):
                self.visit(child_node)
                continue

            # child_node is one of the expression nodes surrounded by {{ }}
            with self.annotate_marker(child_node):
                self.visit(child_node)

        end = self._index
        self.annotate(node, start=start, end=end)

    def visit_Block(self, node: nodes.Block) -> None:
        """Visit a ``Block`` in the stream.

        Examples::

            {% block name %}block{% endblock %}
            {% block name scoped %}block{% endblock %}
            {% block name scoped required %}block{% endblock %}
            {% block name required %}block{% endblock %}
        """
        with self.annotate_marker(node, block="block"):
            ranges = self._whitespace_ranges

            self.seek(node.name)
            self.chomp_to(ranges)
            # jinja parser only supports one order: scoped required
            if node.scoped:
                self.seek("scoped")
                self.chomp_to(ranges)
            if node.required:
                self.seek("required")
                self.chomp_to(ranges)
        for child_node in node.body:
            self.visit(child_node)
        with self.annotate_marker(node, block="endblock"):
            pass

    def visit_Extends(self, node: nodes.Extends) -> None:
        """Visit an ``Extends`` block in the stream.

        Example::

            {% extends name %}
        """
        with self.annotate_marker(node, block="extends"):
            self.visit(node.template)

    def visit_Include(self, node: nodes.Include) -> None:
        """Visit an ``Include`` block in the stream.

        Examples::

            {% include name %}
            {% include name ignore missing %}
            {% include name ignore missing without context %}
            {% include name without context %}
        """
        with self.annotate_marker(node, block="include"):
            ranges = self._whitespace_ranges

            self.visit(node.template)
            self.chomp_to(ranges)
            if node.ignore_missing:
                self.seek("ignore")
                self.chomp_to(ranges)
                self.seek("missing")
                self.chomp_to(ranges)
            # include defaults to "with context"
            index = self._index
            if not node.with_context:
                self.seek("without")
                self.chomp_to(ranges)
                self.seek("context")
            elif "with" == self.stream[index : index + 4]:
                # with context (implicit default) explicitly specified
                self.seek("with")
                self.chomp_to(ranges)
                self.seek("context")

    def visit_Import(self, node: nodes.Import) -> None:
        """Visit an ``Import`` block in the stream.

        Examples::

            {% import expr as name %}
            {% import expr as name without context %}
        """
        with self.annotate_marker(node, block="import"):
            ranges = self._whitespace_ranges

            self.visit(node.template)
            self.chomp_to(ranges)
            self.seek("as")
            self.chomp_to(ranges)
            self.seek(node.target)
            self.chomp_to(ranges)
            # import defaults to "without context"
            index = self._index
            if node.with_context:
                self.seek("with")
                self.chomp_to(ranges)
                self.seek("context")
            elif "without" == self.stream[index : index + 7]:
                # without context (implicit default) explicitly specified
                self.seek("without")
                self.chomp_to(ranges)
                self.seek("context")

    def visit_FromImport(self, node: nodes.FromImport) -> None:
        """Visit a ``FromImport`` block in the stream.

        Examples::

            {% from expr import expr as name %}
            {% from expr import expr as name without context %}
        """
        with self.annotate_marker(node, block="from"):
            ranges = self._whitespace_ranges

            self.visit(node.template)
            self.chomp_to(ranges)
            self.seek("import")
            self.chomp_to(ranges)
            for idx, name in enumerate(node.names):
                if idx:
                    self.seek(",")
                    self.chomp_to(ranges)
                if isinstance(name, tuple):
                    self.seek(name[0])
                    self.chomp_to(ranges)
                    self.seek("as")
                    self.chomp_to(ranges)
                    self.seek(name[1])
                    self.chomp_to(ranges)
                else:  # str
                    self.seek(name)
                    self.chomp_to(ranges)
            # import defaults to "without context"
            index = self._index
            if node.with_context:
                self.seek("with")
                self.chomp_to(ranges)
                self.seek("context")
            elif "without" == self.stream[index : index + 7]:
                # without context (implicit default) explicitly specified
                self.seek("without")
                self.chomp_to(ranges)
                self.seek("context")

    def visit_For(self, node: nodes.For) -> None:
        """Visit a ``For`` block in the stream.

        Examples::

            {% for target in iter %}block{% endfor %}
            {% for target in iter recursive %}block{% endfor %}
            {% for target in iter %}block{% else %}block{% endfor %}
        """
        with self.annotate_marker(node, block="for"):
            ranges = self._whitespace_ranges

            self.visit(node.target)
            self.chomp_to(ranges)
            self.seek("in")
            self.chomp_to(ranges)
            self.visit(node.iter)
            self.chomp_to(ranges)
            if node.test is not None:
                self.seek("if")
                self.chomp_to(ranges)
                self.visit(node.test)
                self.chomp_to(ranges)
            if node.recursive:
                self.seek("recursive")
                self.chomp_to(ranges)
        for child_node in node.body:
            self.visit(child_node)
        if node.else_:
            with self.annotate_marker(node, block="else"):
                pass
            for child_node in node.else_:
                self.visit(child_node)
        with self.annotate_marker(node, block="endfor"):
            pass

    def visit_If(self, node: nodes.If) -> None:
        """Visit an ``If`` block in the stream."""
        with self.annotate_marker(node, block="if"):
            self.visit(node.test)
        for child_node in node.body:
            self.visit(child_node)
        for elif_node in node.elif_:
            with self.annotate_marker(node, block="elif"):
                self.visit(elif_node.test)
            for child_node in elif_node.body:
                self.visit(child_node)
        if node.else_:
            with self.annotate_marker(node, block="else"):
                pass
            for child_node in node.else_:
                self.visit(child_node)
        with self.annotate_marker(node, block="endif"):
            pass

    def visit_With(self, node: nodes.With) -> None:
        """Visit a ``With`` statement (manual scopes) in the stream."""
        with self.annotate_marker(node, block="with"):
            ranges = self._whitespace_ranges

            first = True
            for target, expr in zip(node.targets, node.values):
                if first:
                    first = False
                else:
                    self.seek(",")
                    self.chomp_to(ranges)
                self.visit(target)
                self.chomp_to(ranges)
                self.seek("=")
                self.chomp_to(ranges)
                self.visit(expr)
                self.chomp_to(ranges)
        for child_node in node.body:
            self.visit(child_node)
        with self.annotate_marker(node, block="endwith"):
            pass

    def visit_ExprStmt(self, node: nodes.ExprStmt) -> None:
        """Visit a ``do`` block in the stream.

        ExprStmtExtension
            A ``do`` tag is like a ``print`` statement but doesn't print the return value.
        ExprStmt
            A statement that evaluates an expression and discards the result.
        """
        with self.annotate_marker(node, block="do"):
            self.visit(node.node)

    def visit_Assign(self, node: nodes.Assign) -> None:
        """Visit an ``Assign`` statement in the stream.

        Example::

            {% set var = value %}
        """
        with self.annotate_marker(node, block="set"):
            ranges = self._whitespace_ranges

            self.visit(node.target)
            self.chomp_to(ranges)
            self.seek("=")
            self.chomp_to(ranges)
            self.visit(node.node)

    # noinspection DuplicatedCode
    def visit_AssignBlock(self, node: nodes.AssignBlock) -> None:
        """Visit an ``Assign`` block in the stream.

        Example::

            {% set var %}value{% endset %}
        """
        with self.annotate_marker(node, block="set"):
            self.visit(node.target)
        for child_node in node.body:
            self.visit(child_node)
        with self.annotate_marker(node, block="endset"):
            pass

    # noinspection DuplicatedCode
    def visit_FilterBlock(self, node: nodes.FilterBlock) -> None:
        """Visit a ``Filter`` block in the stream.

        Example::

            {% filter <filter> %}block{% endfilter %}
        """
        with self.annotate_marker(node, block="filter"):
            self.visit(node.filter)
        for child_node in node.body:
            self.visit(child_node)
        with self.annotate_marker(node, block="endfilter"):
            pass

    def visit_Macro(self, node: nodes.Macro) -> None:
        """Visit a ``Macro`` definition block in the stream.

        Example::

            {% macro name(args/defaults) %}block{% endmacro %}
        """
        with self.annotate_marker(node, block="macro"):
            self.seek(node.name)
            self.chomp_to(self._whitespace_ranges)
            self.macro_signature(node)
        for child_node in node.body:
            self.visit(child_node)
        with self.annotate_marker(node, block="endmacro"):
            pass

    def visit_CallBlock(self, node: nodes.CallBlock) -> None:
        """Visit a macro ``Call`` block in the stream.

        Examples::

            {% call macro() %}block{% endcall %}
            {% call(args/defaults) macro() %}block{% endcall %}
        """
        with self.annotate_marker(node, block="call"):
            if node.args:
                self.macro_signature(node)
            self.chomp_to(self._whitespace_ranges)
            self.visit(node.call)
        for child_node in node.body:
            self.visit(child_node)
        with self.annotate_marker(node, block="endcall"):
            pass

    # -- Expression Visitors

    def visit_Name(self, node: nodes.Name) -> None:
        """Visit a ``Name`` expression in the stream."""
        # ctx is one of: load, store, param
        # load named var, store named var, or store named function parameter
        self.simple_seek_and_annotate(node.name, node)

    def visit_NSRef(self, node: nodes.NSRef) -> None:
        """Visit a ref to namespace value assignment in the stream."""
        ranges = []
        start = self._index
        index = self.seek(node.name)
        if start != index:
            ranges.append((start, index))
        self.chomp_to(ranges)
        self.seek(".")
        self.chomp_to(ranges)
        self.seek(node.attr)
        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

    def visit_Const(self, node: nodes.Const) -> None:
        """Visit a constant value (``int``, ``str``, etc) in the stream."""
        # We are using repr() here to handle quoting strings.
        # TODO: handle alt quotes
        self.simple_seek_and_annotate(repr(node.value), node)

    def visit_TemplateData(self, node: nodes.TemplateData) -> None:
        """a constant string (between Jinja blocks)."""
        self.simple_seek_and_annotate(node.data, node)

    def visit_Tuple(self, node: nodes.Tuple) -> None:
        """Visit a ``Tuple`` in the stream."""
        # TODO: handle ctx = load or store
        outer_ranges = self._whitespace_ranges
        ranges = self._whitespace_ranges = []

        start = self._index
        index = self.seek("(")
        if start != index:
            ranges.append((start, index))
        self.chomp_to(ranges)
        for idx, item in enumerate(node.items):
            if idx:
                self.seek(",")
                self.chomp_to(ranges)
            self.visit(item)
            self.chomp_to(ranges)
        if self.stream[self._index] == ",":
            self.seek(",")
            self.chomp_to(ranges)
        self.seek(")")
        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

        self._whitespace_ranges = outer_ranges

    def visit_List(self, node: nodes.List) -> None:
        """Visit a ``List`` in the stream."""
        outer_ranges = self._whitespace_ranges
        ranges = self._whitespace_ranges = []

        start = self._index
        index = self.seek("[")
        if start != index:
            ranges.append((start, index))
        self.chomp_to(ranges)
        for idx, item in enumerate(node.items):
            if idx:
                self.seek(",")
                self.chomp_to(ranges)
            self.visit(item)
            self.chomp_to(ranges)
        if self.stream[self._index] == ",":
            self.seek(",")
            self.chomp_to(ranges)
        self.seek("]")
        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

        self._whitespace_ranges = outer_ranges

    def visit_Dict(self, node: nodes.Dict) -> None:
        """Visit a ``Dict`` in the stream."""
        outer_ranges = self._whitespace_ranges
        ranges = self._whitespace_ranges = []

        start = self._index
        index = self.seek("{")
        if start != index:
            ranges.append((start, index))
        self.chomp_to(ranges)

        item: nodes.Pair
        for idx, item in enumerate(node.items):
            if idx:
                self.seek(",")
                self.chomp_to(ranges)
            self.visit(item.key)
            self.chomp_to(ranges)
            self.seek(":")
            self.chomp_to(ranges)
            self.visit(item.value)
            self.chomp_to(ranges)
        if self.stream[self._index] == ",":
            self.seek(",")
            self.chomp_to(ranges)
        self.seek("}")
        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

        self._whitespace_ranges = outer_ranges

    def _binary_op(self, node: nodes.BinExpr) -> None:
        """Visit a ``BinExpr`` (left and right op) in the stream."""
        outer_ranges = self._whitespace_ranges
        ranges = self._whitespace_ranges = []

        start = self._index
        self.chomp_to(ranges)
        # parentheses might be captured in whitespace

        self.visit(node.left)

        after_left = self._index
        index = self.seek(node.operator)
        if after_left != index:
            ranges.append((after_left, index))
        self.chomp_to(ranges)

        self.visit(node.right)

        self.chomp_to(ranges)
        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

        self._whitespace_ranges = outer_ranges

    visit_Add = _binary_op
    visit_Sub = _binary_op
    visit_Mul = _binary_op
    visit_Div = _binary_op
    visit_FloorDiv = _binary_op
    visit_Pow = _binary_op
    visit_Mod = _binary_op
    visit_And = _binary_op
    visit_Or = _binary_op

    def _unary_op(self, node: nodes.UnaryExpr) -> None:
        """Visit an ``UnaryExpr`` (one node with one op) in the stream."""
        outer_ranges = self._whitespace_ranges
        ranges = self._whitespace_ranges = []

        start = self._index

        index = self.seek(node.operator)
        if start != index:
            ranges.append((start, index))
        self.chomp_to(ranges)

        self.visit(node.node)

        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

        self._whitespace_ranges = outer_ranges

    visit_Pos = _unary_op
    visit_Neg = _unary_op

    def visit_Not(self, node: nodes.Not) -> None:
        """Visit a negated expression in the stream."""
        if isinstance(node.node, nodes.Test):
            return self.visit_Test(node.node, negate=True)
        return self._unary_op(node)

    def visit_Concat(self, node: nodes.Concat) -> None:
        """Visit a string concatenation expression in the stream.

        The Concat operator ``~`` concatenates expressions
        after converting them to strings.
        """
        outer_ranges = self._whitespace_ranges
        ranges = self._whitespace_ranges = []

        start = self._index

        for idx, expr in enumerate(node.nodes):
            if idx:
                self.chomp_to(ranges)
                self.seek("~")
                self.chomp_to(ranges)
            self.visit(expr)

        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

        self._whitespace_ranges = outer_ranges

    def visit_Compare(self, node: nodes.Compare) -> None:
        """Visit a ``Compare`` operator in the stream."""
        outer_ranges = self._whitespace_ranges
        ranges = self._whitespace_ranges = []

        start = self._index
        self.chomp_to(ranges)
        # parentheses might be captured in whitespace

        self.visit(node.expr)
        self.chomp_to(ranges)

        # spell-checker:disable
        for operand in node.ops:
            # node.ops: List[Operand]
            # op.op: eq, ne, gt, gteq, lt, lteq, in, notin
            self.visit(operand)
        # spell-checker:enable

        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

        self._whitespace_ranges = outer_ranges

    def visit_Operand(self, node: nodes.Operand) -> None:
        """Visit an ``Operand`` in the stream."""
        ranges = self._whitespace_ranges

        start = self._index
        index = self.seek(operators[node.op])
        if start != index:
            ranges.append((start, index))
        self.chomp_to(ranges)
        self.visit(node.expr)
        end = self._index

        self.annotate(node, start=start, end=end)

    def visit_Getattr(self, node: nodes.Getattr) -> None:
        """Visit a ``Getattr`` expression in the stream."""
        ranges = self._whitespace_ranges

        start = self._index
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node)
        self.chomp_to(ranges)
        self.seek(".")
        self.chomp_to(ranges)
        self.seek(node.attr)
        end = self._index

        self.annotate(node, start=start, end=end)

    def visit_Getitem(self, node: nodes.Getitem) -> None:
        """Visit a ``Getitem`` expression in the stream."""
        ranges = self._whitespace_ranges

        start = self._index
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node)
        self.chomp_to(ranges)
        self.seek("[")
        self.chomp_to(ranges)
        self.visit(node.arg)
        self.chomp_to(ranges)
        self.seek("]")
        end = self._index

        self.annotate(node, start=start, end=end)

    def visit_Slice(self, node: nodes.Slice) -> None:
        """Visit a ``Slice`` expression in the stream."""
        ranges = self._whitespace_ranges

        start = self._index
        self.chomp_to(ranges)
        if node.start is not None:
            self.visit(node.start)
            self.chomp_to(ranges)
        self.seek(":")
        self.chomp_to(ranges)
        if node.stop is not None:
            self.visit(node.stop)
            self.chomp_to(ranges)
        if node.step is not None:
            self.seek(":")
            self.chomp_to(ranges)
            self.visit(node.step)
            self.chomp_to(ranges)
        end = self._index

        self.annotate(node, start=start, end=end)

    def visit_Filter(self, node: nodes.Filter) -> None:
        """Visit a Jinja ``Filter`` in the stream."""
        outer_ranges = self._whitespace_ranges
        ranges = self._whitespace_ranges = []

        start = self._index
        if node.node is not None:
            self.visit(node.node)
            self.chomp_to(ranges)
            self.seek("|")
            self.chomp_to(ranges)
        before = self._index
        index = self.seek(node.name)
        if before != index:
            ranges.append((before, index))
        self.chomp_to(ranges)
        if any((node.args, node.kwargs, node.dyn_args, node.dyn_kwargs)):
            self.seek("(")
            self.chomp_to(ranges)
            self.signature(node)
            self.chomp_to(ranges)
            self.seek(")")

        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

        self._whitespace_ranges = outer_ranges

    def visit_Test(self, node: nodes.Test, negate: bool = False) -> None:
        """Visit a Jinja ``Test`` in the stream."""
        outer_ranges = self._whitespace_ranges
        ranges = self._whitespace_ranges = []

        start = self._index
        self.visit(node.node)
        self.chomp_to(ranges)
        before = self._index
        index = self.seek("is")
        if before != index:
            ranges.append((before, index))
        self.chomp_to(ranges)
        if negate:
            before = self._index
            index = self.seek("not")
            if before != index:
                ranges.append((before, index))
            self.chomp_to(ranges)
        self.seek(node.name)
        self.chomp_to(ranges)
        if any((node.args, node.kwargs, node.dyn_args, node.dyn_kwargs)):
            self.seek("(")
            self.chomp_to(ranges)
            self.signature(node)
            self.chomp_to(ranges)
            self.seek(")")

        end = self._index
        # Do not chomp; the next AST node handles that.
        self.annotate(node, start=start, end=end, whitespace_ranges=tuple(ranges))

        self._whitespace_ranges = outer_ranges

    def visit_CondExpr(self, node: nodes.CondExpr) -> None:
        """Visit a conditional expression in the stream.

        A conditional expression (inline ``if`` expression)::

            {{ foo if bar else baz }}
        """
        ranges = self._whitespace_ranges

        start = self._index
        self.chomp_to(ranges)
        self.visit(node.expr1)
        self.chomp_to(ranges)
        self.seek("if")
        self.chomp_to(ranges)
        self.visit(node.test)
        self.chomp_to(ranges)
        if node.expr2 is not None:
            self.seek("else")
            self.chomp_to(ranges)
            self.visit(node.expr2)
        end = self._index

        self.annotate(node, start=start, end=end)

    def visit_Call(self, node: nodes.Call) -> None:
        """Visit a function ``Call`` expression in the stream."""
        ranges = self._whitespace_ranges

        start = self._index
        self.chomp_to(ranges)
        self.visit(node.node)
        self.chomp_to(ranges)
        self.seek("(")
        self.chomp_to(ranges)
        self.signature(node)
        self.chomp_to(ranges)
        self.seek(")")
        end = self._index

        self.annotate(node, start=start, end=end)

    def visit_Keyword(self, node: nodes.Keyword) -> None:
        """Visit a dict ``Keyword`` expression in the stream."""
        ranges = self._whitespace_ranges

        start = self._index
        index = self.seek(node.key)
        if start != index:
            ranges.append((start, index))
        self.chomp_to(ranges)
        self.seek("=")
        self.chomp_to(ranges)
        self.visit(node.value)
        end = self._index

        self.annotate(node, start=start, end=end)

    # -- Unused nodes for extensions

    # def visit_MarkSafe(self, node: nodes.MarkSafe) -> None:
    #     """ast node added by extensions, could dump to template if syntax were known"""

    # def visit_MarkSafeIfAutoescape(self, node: nodes.MarkSafeIfAutoescape) -> None:
    #     """Used by InternationalizationExtension"""
    #     # i18n adds blocks: ``trans/pluralize/endtrans``, but they are not in ast

    # def visit_EnvironmentAttribute(self, node: nodes.EnvironmentAttribute) -> None:
    #     """ast node added by extensions, not present in orig template"""

    # def visit_ExtensionAttribute(self, node: nodes.ExtensionAttribute) -> None:
    #     """ast node added by extensions, not present in orig template"""

    # def visit_ImportedName(self, node: nodes.ImportedName) -> None:
    #     """ast node added by extensions, could dump to template if syntax were known"""

    # def visit_InternalName(self, node: nodes.InternalName) -> None:
    #     """ast node added by parser.free_identifier, not present in template"""

    # def visit_ContextReference(self, node: nodes.ContextReference) -> None:
    #     """Added by DebugExtension"""
    #     # triggered by debug block, but debug block is not present in ast

    # def visit_DerivedContextReference(self, node: nodes.DerivedContextReference) -> None:
    #     """could be added by extensions. like debug block but w/ locals"""

    # noinspection PyUnusedLocal
    def visit_Continue(
        self, node: nodes.Continue  # pylint: disable=unused-argument
    ) -> None:
        """Visit a ``Continue`` block for the LoopControlExtension in the stream."""
        with self.annotate_marker(node, block="continue"):
            pass

    # noinspection PyUnusedLocal
    def visit_Break(self, node: nodes.Break) -> None:  # pylint: disable=unused-argument
        """Visit a ``Break`` block for the LoopControlExtension in the stream."""
        with self.annotate_marker(node, block="break"):
            pass

    # def visit_Scope(self, node: nodes.Scope) -> None:
    #     """could be added by extensions.
    #     Wraps the ScopedEvalContextModifier node for autoescape blocks
    #     """

    # def visit_OverlayScope(self, node: nodes.OverlayScope) -> None:
    #     """could be added by extensions."""

    # def visit_EvalContextModifier(self, node: nodes.EvalContextModifier) -> None:
    #     """could be added by extensions."""

    def visit_ScopedEvalContextModifier(
        self, node: nodes.ScopedEvalContextModifier
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
        with self.annotate_marker(node, block="autoescape"):
            self.visit(autoescape)
        for child_node in node.body:
            self.visit(child_node)
        with self.annotate_marker(node, block="endautoescape"):
            pass
