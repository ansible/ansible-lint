"""Jinja template/expression utils for transforms."""

from io import StringIO
from typing import List, Optional, TextIO, Union, cast

from jinja2 import nodes
from jinja2.compiler import operators
from jinja2.environment import Environment
from jinja2.visitor import NodeVisitor


def dump(
    node: nodes.Template,
    environment: Environment,
    stream: Optional[TextIO] = None,
) -> Optional[str]:
    """Dump a jinja2 ast back into a jinja2 template.

    This is based on jinja2.compiler.generate
    """
    if not isinstance(node, nodes.Template):
        raise TypeError("Can't dump non template nodes")

    dumper = TemplateDumper(environment, stream)
    dumper.visit(node)

    if stream is None:
        stream = cast(StringIO, dumper.stream)
        return stream.getvalue()

    return None


# pylint: disable=too-many-public-methods
class TemplateDumper(NodeVisitor):
    """Dump a jinja2 AST back into a jinja2 template.

    This facilitates AST-based template modification.
    This is based on jinja2.compiler.CodeGenerator
    """

    def __init__(
        self,
        environment: Environment,
        stream: Optional[TextIO] = None,
    ):
        """Create a TemplateDumper."""
        if stream is None:
            stream = StringIO()
        self.environment = environment
        self.stream = stream

    # -- Various compilation helpers

    def write(self, x: str) -> None:
        """Write a string into the output stream."""
        self.stream.write(x)

    def signature(
        self,
        node: Union[nodes.Call, nodes.Filter, nodes.Test],
    ) -> None:
        """Write a function call to the stream for the current node."""
        first = True
        arg: nodes.Expr
        for arg in node.args:
            if first:
                first = False
            else:
                self.write(", ")
            self.visit(arg)
        # cast because typehint is incorrect on nodes._FilterTestCommon
        for kwarg in cast(List[nodes.Keyword], node.kwargs):
            if first:
                first = False
            else:
                self.write(", ")
            self.visit(kwarg)
        if node.dyn_args:
            if first:
                first = False
                self.write("*")
            else:
                self.write(", *")
            self.visit(node.dyn_args)
        if node.dyn_kwargs is not None:
            if first:
                self.write("**")
            else:
                self.write(", **")
            self.visit(node.dyn_kwargs)

    def macro_signature(
        self,
        node: Union[nodes.Macro, nodes.CallBlock],
    ) -> None:
        """Write a Macro or CallBlock signature to the stream for the current node."""
        self.write("(")
        for idx, arg in enumerate(node.args):
            if idx:
                self.write(", ")
            self.visit(arg)
            try:
                default = node.defaults[idx - len(node.args)]
            except IndexError:
                continue
            self.write(" = ")
            self.visit(default)
        self.write(")")

    # -- Statement Visitors

    # def visit_Template(self, node: nodes.Template) -> None:
    #     """Template is the root node. Nothing special needed, so use generic_visitor.""
    #     pass

    def visit_Output(self, node: nodes.Template) -> None:
        """Write an Output node to the stream.

        Output is a {{ }} statement (aka `print` or output statement).
        """
        for child_node in node.iter_child_nodes():
            # child_node might be TemplateData which is outside {{ }}
            do_var_wrap = not isinstance(child_node, nodes.TemplateData)
            if do_var_wrap:
                self.write(f"{self.environment.variable_start_string} ")
            self.visit(child_node)
            if do_var_wrap:
                self.write(f" {self.environment.variable_end_string}")

    def visit_Block(self, node: nodes.Block) -> None:
        """Write a Block to the stream.

        {% block name %}block{% endblock %}
        {% block name scoped %}block{% endblock %}
        {% block name scoped required %}block{% endblock %}
        {% block name required %}block{% endblock %}
        """
        self.write(f"{self.environment.block_start_string} block ")
        self.write(node.name)
        if node.scoped:
            self.write(" scoped")
        if node.required:
            self.write(" required")
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endblock {self.environment.block_end_string}"
        )

    def visit_Extends(self, node: nodes.Extends) -> None:
        """Write an Extends block to the stream.

        {% extends name %}
        """
        self.write(f"{self.environment.block_start_string} extends ")
        self.visit(node.template)
        self.write(f" {self.environment.block_end_string}")

    def visit_Include(self, node: nodes.Include) -> None:
        """Write an 'Include' block to the stream.

        {% include name %}
        {% include name ignore missing %}
        {% include name ignore missing without context %}
        {% include name without context %}
        """
        self.write(f"{self.environment.block_start_string} include ")
        self.visit(node.template)
        if node.ignore_missing:
            self.write(" ignore missing")
        # include defaults to "with context" so leave it off
        if not node.with_context:
            self.write(" without context")
        self.write(f" {self.environment.block_end_string}")

    def visit_Import(self, node: nodes.Import) -> None:
        """Write an Import block to the stream.

        {% import expr as name %}
        {% import expr as name without context %}
        """
        self.write(f"{self.environment.block_start_string} import ")
        self.visit(node.template)
        self.write(f" as {node.target}")
        # import defaults to "without context" so leave it off
        if node.with_context:
            self.write(" with context")
        self.write(f" {self.environment.block_end_string}")

    def visit_FromImport(self, node: nodes.FromImport) -> None:
        """Write a FromImport block to the stream.

        {% import expr as name %}
        {% import expr as name without context %}
        """
        self.write(f"{self.environment.block_start_string} from ")
        self.visit(node.template)
        self.write(" import ")
        for idx, name in enumerate(node.names):
            if idx:
                self.write(", ")
            if isinstance(name, tuple):
                self.write(f"{name[0]} as {name[1]}")
            else:  # str
                self.write(name)
        # import defaults to "without context" so leave it off
        if node.with_context:
            self.write(" with context")
        self.write(f" {self.environment.block_end_string}")

    def visit_For(self, node: nodes.For) -> None:
        """Write a For block to the stream.

        {% for target in iter %}block{% endfor %}
        {% for target in iter recursive %}block{% endfor %}
        {% for target in iter %}block{% else %}block{% endfor %}
        """
        self.write(f"{self.environment.block_start_string} for ")
        self.visit(node.target)
        self.write(" in ")
        self.visit(node.iter)
        if node.test is not None:
            self.write(" if ")
            self.visit(node.test)
        if node.recursive:
            self.write(" recursive")
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        if node.else_:
            self.write(
                f"{self.environment.block_start_string} else {self.environment.block_end_string}"
            )
            for child_node in node.else_:
                self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endfor {self.environment.block_end_string}"
        )

    def visit_If(self, node: nodes.If) -> None:
        """Write an If block to the stream."""
        self.write(f"{self.environment.block_start_string} if ")
        self.visit(node.test)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        for elif_node in node.elif_:
            self.write(f"{self.environment.block_start_string} elif ")
            self.visit(elif_node.test)
            self.write(f" {self.environment.block_end_string}")
            for child_node in elif_node.body:
                self.visit(child_node)
        if node.else_:
            self.write(
                f"{self.environment.block_start_string} else {self.environment.block_end_string}"
            )
            for child_node in node.else_:
                self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endif {self.environment.block_end_string}"
        )

    def visit_With(self, node: nodes.With) -> None:
        """Write a With statement (manual scopes) to the stream."""
        self.write(f"{self.environment.block_start_string} with ")
        first = True
        for target, expr in zip(node.targets, node.values):
            if first:
                first = False
            else:
                self.write(", ")
            self.visit(target)
            self.write(" = ")
            self.visit(expr)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endwith {self.environment.block_end_string}"
        )

    def visit_ExprStmt(self, node: nodes.ExprStmt) -> None:
        """Write a do block to the stream.

        ExprStmtExtension: `do` tag like print statement but doesn't print the return value.
        ExprStmt: A statement that evaluates an expression and discards the result.
        """
        self.write(f"{self.environment.block_start_string} do ")
        self.visit(node.node)
        self.write(f" {self.environment.block_end_string}")

    def visit_Assign(self, node: nodes.Assign) -> None:
        """Write an Assign statement to the stream.

        {% set var = value %}
        """
        self.write(f"{self.environment.block_start_string} set ")
        self.visit(node.target)
        self.write(" = ")
        self.visit(node.node)
        self.write(f" {self.environment.block_end_string}")

    # noinspection DuplicatedCode
    def visit_AssignBlock(self, node: nodes.AssignBlock) -> None:
        """Write an Assign block to the stream.

        {% set var %}value{% endset %}
        """
        self.write(f"{self.environment.block_start_string} set ")
        self.visit(node.target)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endset {self.environment.block_end_string}"
        )

    # noinspection DuplicatedCode
    def visit_FilterBlock(self, node: nodes.FilterBlock) -> None:
        """Write a Filter block to the stream.

        {% filter <filter> %}block{% endfilter %}
        """
        self.write(f"{self.environment.block_start_string} filter ")
        self.visit(node.filter)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endfilter {self.environment.block_end_string}"
        )

    def visit_Macro(self, node: nodes.Macro) -> None:
        """Write a Macro definition block to the stream.

        {% macro name(args/defaults) %}block{% endmacro %}
        """
        self.write(f"{self.environment.block_start_string} macro ")
        self.write(node.name)
        self.macro_signature(node)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endmacro {self.environment.block_end_string}"
        )

    def visit_CallBlock(self, node: nodes.CallBlock) -> None:
        """Write a macro Call block to the stream.

        {% call macro() %}block{% endcall %}
        {% call(args/defaults) macro() %}block{% endcall %}
        """
        self.write(f"{self.environment.block_start_string} call")
        if node.args:
            self.macro_signature(node)
        self.write(" ")
        self.visit(node.call)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endcall {self.environment.block_end_string}"
        )

    # -- Expression Visitors

    def visit_Name(self, node: nodes.Name) -> None:
        """Write a Name expression to the stream."""
        # ctx is one of: load, store, param
        # load named var, store named var, or store named function parameter
        self.write(node.name)

    def visit_NSRef(self, node: nodes.NSRef) -> None:
        """Write a ref to namespace value assignment to the stream."""
        self.write(f"{node.name}.{node.attr}")

    def visit_Const(self, node: nodes.Const) -> None:
        """Write a constant value (int, str, etc) to the stream."""
        # We are using repr() here to handle quoting strings.
        self.write(repr(node.value))

    def visit_TemplateData(self, node: nodes.TemplateData) -> None:
        """Write a constant string (between Jinja blocks) to the stream."""
        self.write(node.data)

    def visit_Tuple(self, node: nodes.Tuple) -> None:
        """Write a Tuple to the stream."""
        # TODO: handle ctx = load or store
        self.write("(")
        idx = -1
        for idx, item in enumerate(node.items):
            if idx:
                self.write(", ")
            self.visit(item)
        self.write(",)" if idx == 0 else ")")

    def visit_List(self, node: nodes.List) -> None:
        """Write a List to the stream."""
        self.write("[")
        for idx, item in enumerate(node.items):
            if idx:
                self.write(", ")
            self.visit(item)
        self.write("]")

    def visit_Dict(self, node: nodes.Dict) -> None:
        """Write a Dict to the stream."""
        self.write("{")
        item: nodes.Pair
        for idx, item in enumerate(node.items):
            if idx:
                self.write(", ")
            self.visit(item.key)
            self.write(": ")
            self.visit(item.value)
        self.write("}")

    def _visit_possible_binop(self, node: nodes.Expr) -> None:
        """Wrap binops in parentheses if needed.

        This is not in _binop so that the outermost
        binop does not get wrapped in parentheses.
        """
        if isinstance(node, nodes.BinExpr):
            self.write("(")
            self.visit(node)
            self.write(")")
        else:
            self.visit(node)

    def _binop(self, node: nodes.BinExpr) -> None:
        """Write a BinExpr (left and right op) to the stream."""
        self._visit_possible_binop(node.left)
        self.write(f" {node.operator} ")
        self._visit_possible_binop(node.right)

    visit_Add = _binop
    visit_Sub = _binop
    visit_Mul = _binop
    visit_Div = _binop
    visit_FloorDiv = _binop
    visit_Pow = _binop
    visit_Mod = _binop
    visit_And = _binop
    visit_Or = _binop

    def _unop(self, node: nodes.UnaryExpr) -> None:
        """Write an UnaryExpr (one node with one op) to the stream."""
        self.write(f"{node.operator} ")
        self._visit_possible_binop(node.node)

    visit_Pos = _unop
    visit_Neg = _unop

    def visit_Not(self, node: nodes.Not) -> None:
        """Write a negated expression to the stream."""
        if isinstance(node.node, nodes.Test):
            return self.visit_Test(node.node, negate=True)
        return self._unop(node)

    def visit_Concat(self, node: nodes.Concat) -> None:
        """Write a string concatenation expression to the stream.

        The Concat operator `~` concatenates expressions
        after converting them to strings.
        """
        for idx, expr in enumerate(node.nodes):
            if idx:
                self.write(" ~ ")
            self.visit(expr)

    def visit_Compare(self, node: nodes.Compare) -> None:
        """Write a Compare operator to the stream."""
        self._visit_possible_binop(node.expr)
        for op in node.ops:
            # node.ops: List[Operand]
            # op.op: eq, ne, gt, gteq, lt, lteq, in, notin
            self.visit(op)

    def visit_Operand(self, node: nodes.Operand) -> None:
        """Write an Operand to the stream."""
        self.write(f" {operators[node.op]} ")
        self._visit_possible_binop(node.expr)

    def visit_Getattr(self, node: nodes.Getattr) -> None:
        """Write a Getattr expression to the stream."""
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node)
        self.write(f".{node.attr}")

    def visit_Getitem(self, node: nodes.Getitem) -> None:
        """Write a Getitem expression to the stream."""
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node)
        self.write("[")
        self.visit(node.arg)
        self.write("]")

    def visit_Slice(self, node: nodes.Slice) -> None:
        """Write a Slice expression to the stream."""
        if node.start is not None:
            self.visit(node.start)
        self.write(":")
        if node.stop is not None:
            self.visit(node.stop)
        if node.step is not None:
            self.write(":")
            self.visit(node.step)

    def visit_Filter(self, node: nodes.Filter) -> None:
        """Write a Jinja Filter to the stream."""
        if node.node is not None:
            self.visit(node.node)
            self.write(" | ")
        self.write(node.name)
        if any((node.args, node.kwargs, node.dyn_args, node.dyn_kwargs)):
            self.write("(")
            self.signature(node)
            self.write(")")

    def visit_Test(self, node: nodes.Test, negate: bool = False) -> None:
        """Write a Jinja Test to the stream."""
        self.visit(node.node)
        if negate:
            self.write(" is not ")
        else:
            self.write(" is ")
        self.write(node.name)
        if any((node.args, node.kwargs, node.dyn_args, node.dyn_kwargs)):
            self.write("(")
            self.signature(node)
            self.write(")")

    def visit_CondExpr(self, node: nodes.CondExpr) -> None:
        """Write a conditional expression to the stream.

        A conditional expression (inline if expression).
        {{ foo if bar else baz }}
        """
        self.visit(node.expr1)
        self.write(" if ")
        self.visit(node.test)
        if node.expr2 is not None:
            self.write(" else ")
            self.visit(node.expr2)

    def visit_Call(self, node: nodes.Call) -> None:
        """Write a function Call expression to the stream."""
        self.visit(node.node)
        self.write("(")
        self.signature(node)
        self.write(")")

    def visit_Keyword(self, node: nodes.Keyword) -> None:
        """Write a dict Keyword expression to the stream."""
        self.write(node.key + "=")
        self.visit(node.value)

    # -- Unused nodes for extensions

    # def visit_MarkSafe(self, node: nodes.MarkSafe) -> None:
    #     """ast node added by extensions, could dump to template if syntax were known"""

    # def visit_MarkSafeIfAutoescape(self, node: nodes.MarkSafeIfAutoescape) -> None:
    #     """Used by InternationalizationExtension"""
    #     # i18n adds blocks: `trans/pluralize/endtrans`, but they are not in ast

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
    def visit_Continue(self, node: nodes.Continue) -> None:
        """Write a 'Continue' block for the LoopControlExtension to the stream."""
        self.write(
            f"{self.environment.block_start_string} continue {self.environment.block_end_string}"
        )

    # noinspection PyUnusedLocal
    def visit_Break(self, node: nodes.Break) -> None:
        """Write a 'Break' block for the LoopControlExtension to the stream."""
        self.write(
            f"{self.environment.block_start_string} break {self.environment.block_end_string}"
        )

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
        """Write an autoescape/endautoescape block to the stream."""
        autoescape = None
        for keyword_node in node.options:
            if keyword_node.key == "autoescape":
                autoescape = keyword_node.value
                break
        if autoescape is None:
            # unknown Modifier block
            self.generic_visit(node)
            return
        self.write(f"{self.environment.block_start_string} autoescape ")
        self.visit(autoescape)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endautoescape {self.environment.block_end_string}"
        )
