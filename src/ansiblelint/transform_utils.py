from io import StringIO
from typing import Any, Mapping, Optional, TextIO, Union

from jinja2 import nodes
from jinja2.compiler import operators
from jinja2.environment import Environment
from jinja2.visitor import NodeVisitor


def dump(
    node: nodes.Template,
    environment: Environment,
    name: Optional[str],
    filename: Optional[str],
    stream: Optional[TextIO] = None,
) -> Optional[str]:
    """Dump a jinja2 ast back into a jinja2 template.
    This is based on jinja2.compiler.generate
    """
    if not isinstance(node, nodes.Template):
        raise TypeError("Can't dump non template nodes")

    dumper = TemplateDumper(
        environment, name, filename, stream
    )
    dumper.visit(node)

    if stream is None:
        return dumper.stream.getvalue()

    return None


class TemplateDumper(NodeVisitor):
    """Dump a jinja2 AST back into a jinja2 template.
    This facilitates AST-based template modification.
    This is based on jinja2.compiler.CodeGenerator
    """

    def __init__(
        self,
        environment: Environment,
        name: Optional[str],
        filename: Optional[str],
        stream: Optional[TextIO] = None,
    ):
        if stream is None:
            stream = StringIO()
        self.environment = environment
        self.name = name
        self.filename = filename
        self.stream = stream

    # -- Various compilation helpers

    def write(self, x: str) -> None:
        """Write a string into the output stream."""
        self.stream.write(x)

    def signature(
        self,
        node: Union[nodes.Call, nodes.Filter, nodes.Test],
    ) -> None:
        """Writes a function call to the stream for the current node."""
        first = True
        arg: nodes.Expr
        for arg in node.args:
            if first:
                first = False
            else:
                self.write(", ")
            self.visit(arg)
        kwarg: nodes.Keyword  # typehint is incorrect on nodes._FilterTestCommon
        for kwarg in node.kwargs:
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
    #     # Template is the root node. Nothing special needed, so use generic_visitor.
    #     pass

    def visit_Output(self, node: nodes.Template) -> None:
        # Output is a {{ }} statement (aka `print` or output statement)
        for child_node in node.iter_child_nodes():
            # child_node might be TemplateData which is outside {{ }}
            do_var_wrap = not isinstance(child_node, nodes.TemplateData)
            if do_var_wrap:
                self.write(f"{self.environment.variable_start_string} ")
            self.visit(child_node)
            if do_var_wrap:
                self.write(f" {self.environment.variable_end_string}")

    def visit_Block(self, node: nodes.Block) -> None:
        """
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
        """{% extends name %}"""
        self.write(f"{self.environment.block_start_string} extends ")
        self.visit(node.template)
        self.write(f" {self.environment.block_end_string}")

    def visit_Include(self, node: nodes.Include) -> None:
        """
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
        """
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
        """
        {% import expr as name %}
        {% import expr as name without context %}
        """
        self.write(f"{self.environment.block_start_string} from ")
        self.visit(node.template)
        self.write(f" import ")
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
        """
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
        # with statements (manual scopes)
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
        """
        ExprStmtExtension: `do` tag like print statement but doesn't print the return value.
        ExprStmt: A statement that evaluates an expression and discards the result.
        """
        self.write(f"{self.environment.block_start_string} do ")
        self.visit(node.node)
        self.write(f" {self.environment.block_end_string}")

    def visit_Assign(self, node: nodes.Assign) -> None:
        """{% set var = value %}"""
        self.write(f"{self.environment.block_start_string} set ")
        self.visit(node.target)
        self.write(" = ")
        self.visit(node.node)
        self.write(f" {self.environment.block_end_string}")

    def visit_AssignBlock(self, node: nodes.AssignBlock) -> None:
        """{% set var %}value{% endset %}"""
        self.write(f"{self.environment.block_start_string} set ")
        self.visit(node.target)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endset {self.environment.block_end_string}"
        )

    def visit_FilterBlock(self, node: nodes.FilterBlock) -> None:
        """{% filter <filter> %}block{% endfilter %}"""
        self.write(f"{self.environment.block_start_string} filter ")
        self.visit(node.filter)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endfilter {self.environment.block_end_string}"
        )

    def visit_Macro(self, node: nodes.Macro) -> None:
        """
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
        """
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
        # ctx is one of: load, store, param
        # load named var, store named var, or store named function parameter
        self.write(node.name)

    def visit_NSRef(self, node: nodes.NSRef) -> None:
        # ref to namespace value assignment
        self.write(f"{node.name}.{node.attr}")

    def visit_Const(self, node: nodes.Const) -> None:
        # constant values (int, str, etc)
        # TODO: handle quoting, escaping (maybe repr it?)
        self.write(repr(node.value))

    def visit_TemplateData(self, node: nodes.TemplateData) -> None:
        # constant template string
        self.write(node.data)

    def visit_Tuple(self, node: nodes.Tuple) -> None:
        # TODO: handle ctx = load or store
        self.write("(")
        idx = -1
        for idx, item in enumerate(node.items):
            if idx:
                self.write(", ")
            self.visit(item)
        self.write(",)" if idx == 0 else ")")

    def visit_List(self, node: nodes.List) -> None:
        self.write("[")
        for idx, item in enumerate(node.items):
            if idx:
                self.write(", ")
            self.visit(item)
        self.write("]")

    def visit_Dict(self, node: nodes.Dict) -> None:
        self.write("{")
        item: nodes.Pair
        for idx, item in enumerate(node.items):
            if idx:
                self.write(", ")
            self.visit(item.key)
            self.write(": ")
            self.visit(item.value)
        self.write("}")

    def _visit_possible_binop(self, node: nodes.Expr):
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
        self.write(f"{node.operator} ")
        self._visit_possible_binop(node.node)

    visit_Pos = _unop
    visit_Neg = _unop

    def visit_Not(self, node: nodes.Not) -> None:
        if isinstance(node.node, nodes.Test):
            return self.visit_Test(node.node, negate=True)
        else:
            return self._unop(node)

    def visit_Concat(self, node: nodes.Concat) -> None:
        """The Concat operator `~` concatenates expressions
        after converting them to strings.
        """
        for idx, expr in enumerate(node.nodes):
            if idx:
                self.write(" ~ ")
            self.visit(expr)

    def visit_Compare(self, node: nodes.Compare) -> None:
        self._visit_possible_binop(node.expr)
        for op in node.ops:
            # node.ops: List[Operand]
            # op.op: eq, ne, gt, gteq, lt, lteq, in, notin
            self.visit(op)

    def visit_Operand(self, node: nodes.Operand) -> None:
        self.write(f" {operators[node.op]} ")
        self._visit_possible_binop(node.expr)

    def visit_Getattr(self, node: nodes.Getattr) -> None:
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node)
        self.write(f".{node.attr}")

    def visit_Getitem(self, node: nodes.Getitem) -> None:
        # node.ctx is only ever "load". Not sure this would change if it wasn't.
        self.visit(node.node)
        self.write("[")
        self.visit(node.arg)
        self.write("]")

    def visit_Slice(self, node: nodes.Slice) -> None:
        if node.start is not None:
            self.visit(node.start)
        self.write(":")
        if node.stop is not None:
            self.visit(node.stop)
        if node.step is not None:
            self.write(":")
            self.visit(node.step)

    def visit_Filter(self, node: nodes.Filter) -> None:
        if node.node is not None:
            self.visit(node.node)
            self.write(" | ")
        self.write(node.name)
        if any((node.args, node.kwargs, node.dyn_args, node.dyn_kwargs)):
            self.write("(")
            self.signature(node)
            self.write(")")

    def visit_Test(self, node: nodes.Test, negate=False) -> None:
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
        """A conditional expression (inline if expression).  (``{{
        foo if bar else baz }}``)
        """
        self.visit(node.expr1)
        self.write(" if ")
        self.visit(node.test)
        if node.expr2 is not None:
            self.write(" else ")
            self.visit(node.expr2)

    def visit_Call(self, node: nodes.Call) -> None:
        self.visit(node.node)
        self.write("(")
        self.signature(node)
        self.write(")")

    def visit_Keyword(self, node: nodes.Keyword) -> None:
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

    def visit_Continue(self, node: nodes.Continue) -> None:
        """LoopControlExtension"""
        self.write(
            f"{self.environment.block_start_string} continue {self.environment.block_end_string}"
        )

    def visit_Break(self, node: nodes.Break) -> None:
        """LoopControlExtension"""
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
        """autoescape/endautoescape block"""
        autoescape = None
        for keyword_node in node.options:
            if keyword_node.key == "autoescape":
                autoescape = keyword_node.value
                break
        if autoescape is None:
            # unknown Modifier block
            return self.generic_visit(node)
        self.write(f"{self.environment.block_start_string} autoescape ")
        self.visit(autoescape)
        self.write(f" {self.environment.block_end_string}")
        for child_node in node.body:
            self.visit(child_node)
        self.write(
            f"{self.environment.block_start_string} endautoescape {self.environment.block_end_string}"
        )
