from typing import Any, Callable, Tuple, Type, Union

import pytest

from jinja2 import nodes
from jinja2.environment import Environment
from jinja2.ext import Extension
from jinja2.visitor import NodeVisitor

from ansiblelint.jinja_utils.annotator import annotate

from .jinja_fixtures import CoreTagsFixtures, FilterFixtures, TrimBlocksFixtures, ImportsFixtures, IncludesFixtures, InheritanceFixtures, ExtensionsFixtures


@pytest.mark.parametrize(
    ("template_source", "extensions"),
    (
        ("{{ [{'nested': ({'dict': [('tuple',), ()]}, {})}, {}] }}", ()),
        # these use fixtures from Jinja's test suite:
        (CoreTagsFixtures.simple_for, ()),
        (CoreTagsFixtures.for_else, ()),
        (CoreTagsFixtures.for_else_scoping_item, ()),
        (CoreTagsFixtures.for_empty_blocks, ()),
        (CoreTagsFixtures.for_context_vars, ()),
        (CoreTagsFixtures.for_cycling, ()),
        (CoreTagsFixtures.for_lookaround, ()),
        (CoreTagsFixtures.for_changed, ()),
        (CoreTagsFixtures.for_scope, ()),
        (CoreTagsFixtures.for_varlen, ()),
        (CoreTagsFixtures.for_recursive, ()),
        (CoreTagsFixtures.for_recursive_lookaround, ()),
        (CoreTagsFixtures.for_recursive_depth0, ()),
        (CoreTagsFixtures.for_recursive_depth, ()),
        (CoreTagsFixtures.for_looploop, ()),
        (CoreTagsFixtures.for_reversed_bug, ()),
        (CoreTagsFixtures.for_loop_errors, ()),
        (CoreTagsFixtures.for_loop_filter_1, ()),
        (CoreTagsFixtures.for_loop_filter_2, ()),
        (CoreTagsFixtures.for_scoped_special_var, ()),
        (CoreTagsFixtures.for_scoped_loop_var_1, ()),
        (CoreTagsFixtures.for_scoped_loop_var_2, ()),
        (CoreTagsFixtures.for_recursive_empty_loop_iter, ()),
        (CoreTagsFixtures.for_call_in_loop, ()),
        (CoreTagsFixtures.for_scoping_bug, ()),
        (CoreTagsFixtures.for_unpacking, ()),
        (CoreTagsFixtures.for_intended_scoping_with_set_1, ()),
        (CoreTagsFixtures.for_intended_scoping_with_set_2, ()),
        (CoreTagsFixtures.simple_if, ()),
        (CoreTagsFixtures.if_elif, ()),
        (CoreTagsFixtures.if_elif_deep, ()),
        (CoreTagsFixtures.if_else, ()),
        (CoreTagsFixtures.if_empty, ()),
        (CoreTagsFixtures.if_complete, ()),
        (CoreTagsFixtures.if_no_scope_1, ()),
        (CoreTagsFixtures.if_no_scope_2, ()),
        (CoreTagsFixtures.simple_macros, ()),
        (CoreTagsFixtures.macros_scoping, ()),
        (CoreTagsFixtures.macros_arguments, ()),
        (CoreTagsFixtures.macros_varargs, ()),
        (CoreTagsFixtures.macros_simple_call, ()),
        (CoreTagsFixtures.macros_complex_call, ()),
        (CoreTagsFixtures.macros_caller_undefined, ()),
        (CoreTagsFixtures.macros_include, ()),
        (CoreTagsFixtures.macros_macro_api, ()),
        (CoreTagsFixtures.macros_callself, ()),
        (CoreTagsFixtures.macros_macro_defaults_self_ref, ()),
        (CoreTagsFixtures.set_normal, ()),
        (CoreTagsFixtures.set_block, ()),
        (CoreTagsFixtures.set_block_escaping, ()),
        (CoreTagsFixtures.set_namespace, ()),
        (CoreTagsFixtures.set_namespace_block, ()),
        (CoreTagsFixtures.set_init_namespace, ()),
        (CoreTagsFixtures.set_namespace_loop, ()),
        (CoreTagsFixtures.set_namespace_macro, ()),
        (CoreTagsFixtures.set_block_escaping_filtered, ()),
        (CoreTagsFixtures.set_block_filtered, ()),
        (CoreTagsFixtures.with_with, ()),
        (CoreTagsFixtures.with_with_argument_scoping, ()),
        (FilterFixtures.groupby, ()),
        (FilterFixtures.groupby_tuple_index, ()),
        (TrimBlocksFixtures.trim, ()),
        (TrimBlocksFixtures.no_trim, ()),
        (TrimBlocksFixtures.no_trim_outer, ()),
        (TrimBlocksFixtures.lstrip_no_trim, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_block1, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_block2, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_comment1, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_comment2, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_raw1, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_raw2, ()),
        (TrimBlocksFixtures.trim_nested, ()),
        (TrimBlocksFixtures.no_trim_nested, ()),
        (TrimBlocksFixtures.comment_trim, ()),
        (TrimBlocksFixtures.comment_no_trim, ()),
        (TrimBlocksFixtures.multiple_comment_trim_lstrip, ()),
        (TrimBlocksFixtures.multiple_comment_no_trim_lstrip, ()),
        (TrimBlocksFixtures.raw_trim_lstrip, ()),
        (TrimBlocksFixtures.raw_no_trim_lstrip, ()),
        # ^^ 79 tests
        (ImportsFixtures.context_imports_1, ()),
        (ImportsFixtures.context_imports_2, ()),
        (ImportsFixtures.context_imports_3, ()),
        (ImportsFixtures.context_imports_4, ()),
        (ImportsFixtures.context_imports_5, ()),
        (ImportsFixtures.context_imports_6, ()),
        (ImportsFixtures.import_needs_name_1, ()),
        (ImportsFixtures.import_needs_name_2, ()),
        (ImportsFixtures.trailing_comma_with_context_1, ()),
        (ImportsFixtures.trailing_comma_with_context_2, ()),
        (ImportsFixtures.trailing_comma_with_context_3, ()),
        (ImportsFixtures.trailing_comma_with_context_4, ()),
        (ImportsFixtures.trailing_comma_with_context_5, ()),
        (ImportsFixtures.exports, ()),
        (ImportsFixtures.import_with_globals, ()),
        (ImportsFixtures.import_with_globals_override, ()),
        (ImportsFixtures.from_import_with_globals, ()),
        (IncludesFixtures.context_include_1, ()),
        (IncludesFixtures.context_include_2, ()),
        (IncludesFixtures.context_include_3, ()),
        (IncludesFixtures.choice_includes_1, ()),
        (IncludesFixtures.choice_includes_2, ()),
        (IncludesFixtures.choice_includes_4, ()),
        (IncludesFixtures.choice_includes_5, ()),
        (IncludesFixtures.choice_includes_6, ()),
        (IncludesFixtures.choice_includes_7, ()),
        (IncludesFixtures.choice_includes_8, ()),
        (IncludesFixtures.include_ignoring_missing_2, ()),
        (IncludesFixtures.include_ignoring_missing_3, ()),
        (IncludesFixtures.include_ignoring_missing_4, ()),
        (IncludesFixtures.context_include_with_overrides_main, ()),
        (IncludesFixtures.context_include_with_overrides_item, ()),
        (IncludesFixtures.unoptimized_scopes, ()),
        (IncludesFixtures.import_from_with_context_a, ()),
        (IncludesFixtures.import_from_with_context, ()),
        (InheritanceFixtures.layout, ()),
        (InheritanceFixtures.level1, ()),
        (InheritanceFixtures.level2, ()),
        (InheritanceFixtures.level3, ()),
        (InheritanceFixtures.level4, ()),
        (InheritanceFixtures.working, ()),
        (InheritanceFixtures.double_e, ()),
        (InheritanceFixtures.super_a, ()),
        (InheritanceFixtures.super_b, ()),
        (InheritanceFixtures.super_c, ()),
        (InheritanceFixtures.reuse_blocks, ()),
        (InheritanceFixtures.preserve_blocks_a, ()),
        (InheritanceFixtures.preserve_blocks_b, ()),
        (InheritanceFixtures.dynamic_inheritance_default1, ()),
        (InheritanceFixtures.dynamic_inheritance_default2, ()),
        (InheritanceFixtures.dynamic_inheritance_child, ()),
        (InheritanceFixtures.multi_inheritance_default1, ()),
        (InheritanceFixtures.multi_inheritance_default2, ()),
        (InheritanceFixtures.multi_inheritance_child, ()),
        (InheritanceFixtures.scoped_block_default_html, ()),
        (InheritanceFixtures.scoped_block, ()),
        (InheritanceFixtures.super_in_scoped_block_default_html, ()),
        (InheritanceFixtures.super_in_scoped_block, ()),
        (InheritanceFixtures.scoped_block_after_inheritance_layout_html, ()),
        (InheritanceFixtures.scoped_block_after_inheritance_index_html, ()),
        (InheritanceFixtures.scoped_block_after_inheritance_helpers_html, ()),
        (InheritanceFixtures.level1_required_default, ()),
        (InheritanceFixtures.level1_required_level1, ()),
        (InheritanceFixtures.level2_required_default, ()),
        (InheritanceFixtures.level2_required_level1, ()),
        (InheritanceFixtures.level2_required_level2, ()),
        (InheritanceFixtures.level3_required_default, ()),
        (InheritanceFixtures.level3_required_level1, ()),
        (InheritanceFixtures.level3_required_level2, ()),
        (InheritanceFixtures.level3_required_level3, ()),
        (InheritanceFixtures.required_with_scope_default1, ()),
        (InheritanceFixtures.required_with_scope_child1, ()),
        # The annotator only supports 'autoescape', 'loopcontrols', and 'do' extensions
        (ExtensionsFixtures.extend_late, ()),
        (ExtensionsFixtures.loop_controls_1, ("jinja2.ext.loopcontrols",)),
        (ExtensionsFixtures.loop_controls_2, ("jinja2.ext.loopcontrols",)),
        (ExtensionsFixtures.do, ("jinja2.ext.do",)),
        (ExtensionsFixtures.auto_escape_scoped_setting_1, ()),
        (ExtensionsFixtures.auto_escape_scoped_setting_2, ()),
        (ExtensionsFixtures.auto_escape_nonvolatile_1, ()),
        (ExtensionsFixtures.auto_escape_nonvolatile_2, ()),
        (ExtensionsFixtures.auto_escape_volatile, ()),
        (ExtensionsFixtures.auto_escape_scoping, ()),
        (ExtensionsFixtures.auto_escape_volatile_scoping, ()),
        # The annotator does not support jinja extensions that do custom parsing
        # (ExtensionsFixtures.extension_nodes, (ExampleExtension,)),
        # (ExtensionsFixtures.contextreference_node_passes_context, (ExampleExtension,)),
        # (ExtensionsFixtures.contextreference_node_can_pass_locals, (DerivedExampleExtension,)),
        # (ExtensionsFixtures.preprocessor_extension, (PreprocessorExtension,)),
        # (ExtensionsFixtures.streamfilter_extension, (StreamFilterExtension)),
        # (ExtensionsFixtures.debug, ("jinja2.ext.debug",)),
        # (ExtensionsFixtures.scope, (ScopeExt)),
        # (ExtensionsFixtures.auto_escape_overlay_scopes, (MagicScopesExtension)),
    ),
)
def test_annotate(jinja_env: Environment, template_source: str, extensions: Tuple[Union[str, Type[Extension]]]):
    for extension in extensions:
        jinja_env.add_extension(extension)

    ast = jinja_env.parse(template_source)
    annotate(ast, jinja_env, raw_template=template_source)

    class TestVisitor(NodeVisitor):
        def generic_visit(self, node: nodes.Node, *args: Any, **kwargs: Any) -> Any:
            """Called if no explicit visitor function exists for a node."""
            for child_node in node.iter_child_nodes():
                kwargs["parent"] = node
                self.visit(child_node, *args, **kwargs)

        def visit(self, node: nodes.Node, *args: Any, **kwargs: Any):
            # TODO: make it easier to identify which node had failures
            assert hasattr(node, "tokens")
            assert isinstance(node.tokens, tuple)
            assert len(node.tokens) == 2
            assert all(isinstance(index, int) for index in node.tokens)
            assert node.tokens[0] < node.tokens[1]
            if "parent" in kwargs:
                # only the root node will not have a parent arg.
                parent: nodes.Node = kwargs["parent"]
                assert hasattr(parent, "tokens")
                assert isinstance(parent.tokens, tuple)
                assert parent.tokens[0] <= node.tokens[0]
                assert node.tokens[1] <= parent.tokens[1]
            super().visit(node, *args, **kwargs)

    TestVisitor().visit(ast)
