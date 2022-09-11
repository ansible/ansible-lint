"""Jinja template String representation."""
from __future__ import annotations

from typing import Any, Literal

from jinja2 import Environment
from jinja2 import nodes as jinja_nodes
from ruamel.yaml import nodes as yaml_nodes
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.scalarstring import ScalarString

from .annotator import annotate
from .dumper import dump


class JinjaTemplate(ScalarString):
    """A str subclass that facilitates lazy AST-based dumping.

    This is used by the Transformer to wrap Jinja templates in YAML documents.
    The string itself is the original template as read from the YAML file.
    The ast attribute contains the AST that rule transforms can modify.
    Then, when the transformer dumps the YAML file, it will also use a template
    dumped from the modified Jinja AST instead of using the original template string.
    """

    # we extend the ruamel.yaml ScalarString which uses __slots__, so we do too.
    __slots__ = ("_ast", "implicit", "_jinja_env", "style", "comment")

    _ast: jinja_nodes.Template | None
    implicit: bool  # True for 'when' keywords that are implicitly Jinja2 expressions
    _jinja_env: Environment
    style: Literal["|", ">", "'", '"', ""]  # allows setting yaml style for template
    comment: str

    def __new__(
        cls,
        value: Any,
        jinja_env: Environment,
        implicit: bool = False,
        anchor: Any = None,
    ) -> JinjaTemplate:
        """Create a new JinjaTemplate ScalarString for use in yaml docs."""
        instance = ScalarString.__new__(cls, value, anchor=anchor)
        instance.implicit = implicit
        instance._ast = None
        instance._jinja_env = jinja_env
        return instance

    @property
    def ast(self) -> jinja_nodes.Template:
        """Return the Jinja AST parsed from this template."""
        if self._ast is None:
            ast = self._jinja_env.parse(self)
            self._ast = annotate(ast, self._jinja_env, raw_template=self)
        return self._ast

    def dump(
        self, max_line_length: int, max_first_line_length: int = None
    ) -> JinjaTemplate:
        """Dump the Jinja AST (possibly modified) back into a template."""
        value = dump(
            self.ast,
            environment=self._jinja_env,
            max_line_length=max_line_length,
            max_first_line_length=max_first_line_length,
        )
        ret = JinjaTemplate(value, self._jinja_env, self.implicit, self.anchor)
        if hasattr(self, "style"):
            ret.style = self.style
        if hasattr(self, "comment"):
            ret.comment = self.comment
        return ret

    @staticmethod
    def represent_jinja_template_scalar(
        representer: RoundTripRepresenter, data: JinjaTemplate
    ) -> yaml_nodes.ScalarNode:
        """Create a ScalarNode for this JinjaTemplate.

        At this point, the node wraps the data object, but any str() ops on it will
        return the original template, not the modified AST.

        The serializer/emitter will have to handle calling data.dump() because
        the Representer does not have info about available line length.
        """
        tag = "tag:yaml.org,2002:str"
        style = getattr(data, "style", None)
        anchor = data.yaml_anchor(any=True)
        node: yaml_nodes.ScalarNode = representer.represent_scalar(
            tag, data, style=style, anchor=anchor
        )
        return node
