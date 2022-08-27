from typing import Literal, Tuple

import pytest
from jinja2 import lexer as j2tokens
from jinja2.lexer import Lexer

from ansiblelint.jinja_utils.token import BEGIN_TOKENS, END_TOKENS, Tokens

from .jinja_fixtures import CoreTagsFixtures, FilterFixtures, TrimBlocksFixtures, ImportsFixtures, IncludesFixtures, InheritanceFixtures, ExtensionsFixtures


@pytest.mark.parametrize(
    ("template_source", "jinja_token_count", "token_pairs_count", "expected_chomps"),
    (
        ("{{ [{'nested': ({'dict': [('tuple',), ()]}, {})}, {}] }}", 29, 10, ()),
        # these use fixtures from Jinja's test suite:
        (CoreTagsFixtures.simple_for, 12, 3, ()),
        (CoreTagsFixtures.for_else, 14, 3, ()),
        (CoreTagsFixtures.for_else_scoping_item, 16, 5, ()),
        (CoreTagsFixtures.for_empty_blocks, 14, 3, ()),
        (CoreTagsFixtures.for_context_vars, 51, 9, ("-",)),
        (CoreTagsFixtures.for_cycling, 37, 8, ()),
        (CoreTagsFixtures.for_lookaround, 35, 7, ("-", "-")),
        (CoreTagsFixtures.for_changed, 18, 4, ("-", "-")),
        (CoreTagsFixtures.for_scope, 12, 3, ()),
        (CoreTagsFixtures.for_varlen, 12, 3, ()),
        (CoreTagsFixtures.for_recursive, 36, 7, ("-", "-")),
        (CoreTagsFixtures.for_recursive_lookaround, 68, 9, ("-", "-")),
        (CoreTagsFixtures.for_recursive_depth0, 42, 8, ("-", "-")),
        (CoreTagsFixtures.for_recursive_depth, 42, 8, ("-", "-")),
        (CoreTagsFixtures.for_looploop, 37, 7, ("-", "-", "-", "-", "-")),
        (CoreTagsFixtures.for_reversed_bug, 23, 5, ()),
        (CoreTagsFixtures.for_loop_errors, 17, 5, ()),
        (CoreTagsFixtures.for_loop_filter_1, 21, 4, ()),
        (CoreTagsFixtures.for_loop_filter_2, 27, 5, ("-",)),
        (CoreTagsFixtures.for_scoped_special_var, 31, 6, ()),
        (CoreTagsFixtures.for_scoped_loop_var_1, 23, 5, ()),
        (CoreTagsFixtures.for_scoped_loop_var_2, 23, 5, ()),
        (CoreTagsFixtures.for_recursive_empty_loop_iter, 10, 2, ("-", "-", "-", "-")),
        (
            CoreTagsFixtures.for_call_in_loop,
            43,
            12,
            ("-", "-", "-", "-", "-", "-", "-", "-", "-"),
        ),
        (CoreTagsFixtures.for_scoping_bug, 35, 9, ("-", "-", "-", "-")),
        (CoreTagsFixtures.for_unpacking, 32, 7, ()),
        (CoreTagsFixtures.for_intended_scoping_with_set_1, 21, 5, ()),
        (CoreTagsFixtures.for_intended_scoping_with_set_2, 27, 6, ()),
        (CoreTagsFixtures.simple_if, 8, 2, ()),
        (CoreTagsFixtures.if_elif, 17, 4, ()),
        (CoreTagsFixtures.if_elif_deep, 7007, 1002, ()),
        (CoreTagsFixtures.if_else, 12, 3, ()),
        (CoreTagsFixtures.if_empty, 12, 3, ()),
        (CoreTagsFixtures.if_complete, 24, 5, ()),
        (CoreTagsFixtures.if_no_scope_1, 16, 4, ()),
        (CoreTagsFixtures.if_no_scope_2, 16, 4, ()),
        (CoreTagsFixtures.simple_macros, 21, 6, ()),
        (CoreTagsFixtures.macros_scoping, 39, 12, ()),
        (CoreTagsFixtures.macros_arguments, 67, 15, ()),
        (CoreTagsFixtures.macros_varargs, 27, 7, ()),
        (CoreTagsFixtures.macros_simple_call, 26, 8, ()),
        (CoreTagsFixtures.macros_complex_call, 32, 10, ()),
        (CoreTagsFixtures.macros_caller_undefined, 26, 7, ()),
        (CoreTagsFixtures.macros_include, 12, 3, ()),
        (CoreTagsFixtures.macros_macro_api, 41, 13, ()),
        (CoreTagsFixtures.macros_callself, 37, 10, ()),
        (CoreTagsFixtures.macros_macro_defaults_self_ref, 35, 7, ("-", "-", "-")),
        (CoreTagsFixtures.set_normal, 9, 2, ()),
        (CoreTagsFixtures.set_block, 11, 3, ()),
        (CoreTagsFixtures.set_block_escaping, 16, 4, ()),
        (CoreTagsFixtures.set_namespace, 21, 4, ()),
        (CoreTagsFixtures.set_namespace_block, 23, 5, ()),
        (CoreTagsFixtures.set_init_namespace, 38, 6, ()),
        (CoreTagsFixtures.set_namespace_loop, 45, 9, ()),
        (CoreTagsFixtures.set_namespace_macro, 51, 11, ()),
        (CoreTagsFixtures.set_block_escaping_filtered, 18, 4, ()),
        (CoreTagsFixtures.set_block_filtered, 17, 3, ()),
        (CoreTagsFixtures.with_with, 30, 6, ("-", "-")),
        (CoreTagsFixtures.with_with_argument_scoping, 44, 7, ("-", "-", "-", "-")),
        (FilterFixtures.groupby, 81, 13, ("-", "-", "-")),
        (FilterFixtures.groupby_tuple_index, 53, 11, ("-", "-", "-")),
        (TrimBlocksFixtures.trim, 9, 2, ()),
        (TrimBlocksFixtures.no_trim, 9, 2, ("+",)),
        (TrimBlocksFixtures.no_trim_outer, 9, 2, ("+",)),
        (TrimBlocksFixtures.lstrip_no_trim, 9, 2, ("+",)),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_block1, 9, 2, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_block2, 9, 2, ("+",)),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_comment1, 2, 1, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_comment2, 2, 1, ("+",)),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_raw1, 2, 1, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_raw2, 2, 1, ("+",)),
        (TrimBlocksFixtures.trim_nested, 18, 4, ()),
        (TrimBlocksFixtures.no_trim_nested, 18, 4, ("+", "+", "+")),
        (TrimBlocksFixtures.comment_trim, 2, 1, ()),
        (TrimBlocksFixtures.comment_no_trim, 2, 1, ("+",)),
        (TrimBlocksFixtures.multiple_comment_trim_lstrip, 4, 3, ()),
        (TrimBlocksFixtures.multiple_comment_no_trim_lstrip, 4, 3, ("+", "+", "+")),
        (TrimBlocksFixtures.raw_trim_lstrip, 8, 3, ()),
        (TrimBlocksFixtures.raw_no_trim_lstrip, 8, 3, ("+",)),
        # ^^ 79 tests
        (ImportsFixtures.context_imports_1, 13, 3, ()),
        (ImportsFixtures.context_imports_2, 15, 3, ()),
        (ImportsFixtures.context_imports_3, 15, 3, ()),
        (ImportsFixtures.context_imports_4, 11, 3, ()),
        (ImportsFixtures.context_imports_5, 13, 3, ()),
        (ImportsFixtures.context_imports_6, 13, 3, ()),
        (ImportsFixtures.import_needs_name_1, 6, 1, ()),
        (ImportsFixtures.import_needs_name_2, 8, 1, ()),
        (ImportsFixtures.trailing_comma_with_context_1, 10, 1, ()),
        (ImportsFixtures.trailing_comma_with_context_2, 11, 1, ()),
        (ImportsFixtures.trailing_comma_with_context_3, 9, 1, ()),
        (ImportsFixtures.trailing_comma_with_context_4, 10, 1, ()),
        (ImportsFixtures.trailing_comma_with_context_5, 10, 1, ()),
        (ImportsFixtures.exports, 53, 13, ()),
        (ImportsFixtures.import_with_globals, 13, 3, ()),
        (ImportsFixtures.import_with_globals_override, 19, 4, ()),
        (ImportsFixtures.from_import_with_globals, 11, 3, ()),
        (IncludesFixtures.context_include_1, 4, 1, ()),
        (IncludesFixtures.context_include_2, 6, 1, ()),
        (IncludesFixtures.context_include_3, 6, 1, ()),
        (IncludesFixtures.choice_includes_1, 8, 2, ()),
        (IncludesFixtures.choice_includes_2, 10, 2, ()),
        (IncludesFixtures.choice_includes_4, 8, 2, ()),
        (IncludesFixtures.choice_includes_5, 4, 1, ()),
        (IncludesFixtures.choice_includes_6, 8, 2, ()),
        (IncludesFixtures.choice_includes_7, 4, 1, ()),
        (IncludesFixtures.choice_includes_8, 6, 2, ()),
        (IncludesFixtures.include_ignoring_missing_2, 6, 1, ()),
        (IncludesFixtures.include_ignoring_missing_3, 8, 1, ()),
        (IncludesFixtures.include_ignoring_missing_4, 8, 1, ()),
        (IncludesFixtures.context_include_with_overrides_main, 19, 4, ()),
        (IncludesFixtures.context_include_with_overrides_item, 3, 1, ()),
        (IncludesFixtures.unoptimized_scopes, 42, 11, ()),
        (IncludesFixtures.import_from_with_context_a, 12, 4, ()),
        (IncludesFixtures.import_from_with_context, 19, 4, ()),
        (InheritanceFixtures.layout, 35, 8, ()),
        (InheritanceFixtures.level1, 12, 3, ()),
        (InheritanceFixtures.level2, 19, 5, ()),
        (InheritanceFixtures.level3, 20, 5, ()),
        (InheritanceFixtures.level4, 12, 3, ()),
        (InheritanceFixtures.working, 29, 7, ()),
        (InheritanceFixtures.double_e, 33, 8, ()),
        (InheritanceFixtures.super_a, 18, 4, ()),
        (InheritanceFixtures.super_b, 18, 5, ()),
        (InheritanceFixtures.super_c, 32, 9, ()),
        (InheritanceFixtures.reuse_blocks, 24, 6, ()),
        (InheritanceFixtures.preserve_blocks_a, 22, 6, ()),
        (InheritanceFixtures.preserve_blocks_b, 17, 5, ()),
        (InheritanceFixtures.dynamic_inheritance_default1, 8, 2, ()),
        (InheritanceFixtures.dynamic_inheritance_default2, 8, 2, ()),
        (InheritanceFixtures.dynamic_inheritance_child, 12, 3, ()),
        (InheritanceFixtures.multi_inheritance_default1, 8, 2, ()),
        (InheritanceFixtures.multi_inheritance_default2, 8, 2, ()),
        (InheritanceFixtures.multi_inheritance_child, 26, 7, ()),
        (InheritanceFixtures.scoped_block_default_html, 19, 4, ()),
        (InheritanceFixtures.scoped_block, 14, 4, ()),
        (InheritanceFixtures.super_in_scoped_block_default_html, 22, 5, ()),
        (InheritanceFixtures.super_in_scoped_block, 22, 6, ()),
        (InheritanceFixtures.scoped_block_after_inheritance_layout_html, 9, 2, ()),
        (InheritanceFixtures.scoped_block_after_inheritance_index_html, 57, 11, ("-",)),
        (InheritanceFixtures.scoped_block_after_inheritance_helpers_html, 17, 4, ()),
        (InheritanceFixtures.level1_required_default, 9, 3, ()),
        (InheritanceFixtures.level1_required_level1, 12, 3, ()),
        (InheritanceFixtures.level2_required_default, 8, 2, ()),
        (InheritanceFixtures.level2_required_level1, 12, 3, ()),
        (InheritanceFixtures.level2_required_level2, 12, 3, ()),
        (InheritanceFixtures.level3_required_default, 8, 2, ()),
        (InheritanceFixtures.level3_required_level1, 4, 1, ()),
        (InheritanceFixtures.level3_required_level2, 12, 3, ()),
        (InheritanceFixtures.level3_required_level3, 4, 1, ()),
        (InheritanceFixtures.required_with_scope_default1, 20, 4, ()),
        (InheritanceFixtures.required_with_scope_child1, 14, 4, ()),
        (ExtensionsFixtures.extend_late, 10, 3, ()),
        (ExtensionsFixtures.loop_controls_1, 34, 7, ("-", "-", "-", "-")),
        (ExtensionsFixtures.loop_controls_2, 32, 7, ("-", "-", "-", "-")),
        (ExtensionsFixtures.do, 37, 8, ("-", "-", "-", "-")),
        (ExtensionsFixtures.extension_nodes, 3, 1, ()),
        (ExtensionsFixtures.contextreference_node_passes_context, 9, 2, ()),
        (ExtensionsFixtures.contextreference_node_can_pass_locals, 14, 4, ()),
        # (ExtensionsFixtures.preprocessor_extension, 1, 0, ()),  # odd
        # (ExtensionsFixtures.streamfilter_extension, 1, 0, ()),  # odd
        (ExtensionsFixtures.debug, 5, 1, ()),
        (ExtensionsFixtures.scope, 44, 7, ("-", "-", "-", "-")),
        (ExtensionsFixtures.auto_escape_scoped_setting_1, 22, 5, ()),
        (ExtensionsFixtures.auto_escape_scoped_setting_2, 22, 5, ()),
        (ExtensionsFixtures.auto_escape_nonvolatile_1, 11, 2, ()),
        (ExtensionsFixtures.auto_escape_nonvolatile_2, 18, 4, ()),
        (ExtensionsFixtures.auto_escape_volatile, 18, 4, ()),
        (ExtensionsFixtures.auto_escape_scoping, 22, 6, ()),
        (ExtensionsFixtures.auto_escape_volatile_scoping, 40, 9, ()),
        (ExtensionsFixtures.auto_escape_overlay_scopes, 42, 10, ("-", "-", "-", "-", "-", "-")),
    ),
)
def test_tokens_iterator(
    lexer: Lexer,
    template_source: str,
    jinja_token_count: int,
    token_pairs_count: int,
    expected_chomps: Tuple[Literal["+", "-"], ...],
):
    tokens = Tokens(lexer, template_source)
    tokens_count = len(tokens)
    last_index = tokens_count - 1

    for i, token in enumerate(tokens):
        assert token.index == i
        assert token.start_pos <= token.end_pos

        if i == 0:
            assert token.token == j2tokens.TOKEN_INITIAL
            assert token.start_pos == 0
            assert token.end_pos == 0
            assert token.pair is None
            assert token.chomp == ""
            continue
        elif i == last_index:
            assert token.token == j2tokens.TOKEN_EOF
            assert token.end_pos == len(template_source)
            assert token.pair is None
            assert token.chomp == ""

        prev_token = tokens[i - 1]
        assert prev_token.end_pos <= token.start_pos
        if i < last_index:
            next_token = tokens[i + 1]
            assert token.end_pos <= next_token.start_pos

        if token.pair is None:
            assert token.chomp == ""
        else:
            assert token.chomp in ("+", "-", "")

            assert token.pair != token
            assert token.pair.pair is not None
            assert token.pair.pair == token
            if token.token == j2tokens.TOKEN_OPERATOR and token.jinja_token.type in (
                j2tokens.TOKEN_LBRACKET,
                j2tokens.TOKEN_RBRACKET,
                j2tokens.TOKEN_LBRACE,
                j2tokens.TOKEN_RBRACE,
                j2tokens.TOKEN_LPAREN,
                j2tokens.TOKEN_RPAREN,
            ):
                for left, right in (
                    (j2tokens.TOKEN_LBRACKET, j2tokens.TOKEN_RBRACKET),
                    (j2tokens.TOKEN_LBRACE, j2tokens.TOKEN_RBRACE),
                    (j2tokens.TOKEN_LPAREN, j2tokens.TOKEN_RPAREN),
                ):
                    if token.jinja_token.type == left:
                        assert token.pair.jinja_token.type == right
                        break
                    if token.jinja_token.type == right:
                        assert token.pair.jinja_token.type == left
                        break
            elif token.token in BEGIN_TOKENS + END_TOKENS:
                for left, right in zip(BEGIN_TOKENS, END_TOKENS):
                    if token.token == left:
                        assert token.pair.token == right
                        break
                    if token.token == right:
                        assert token.pair.token == left
                        break

    # jinja_token is None if lexer.wrap() skips it (eg whitespace)
    jinja_tokens = [t.jinja_token for t in tokens if t.jinja_token is not None]
    assert len(jinja_tokens) == jinja_token_count

    pairs = [t for t in tokens if t.pair is not None]
    assert len(pairs) / 2 == token_pairs_count

    chomps = tuple(t.chomp for t in tokens if t.chomp)
    assert chomps == expected_chomps
