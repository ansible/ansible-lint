"""Tests for expanded Jinja tokens iteration."""
from __future__ import annotations

from typing import Literal

import pytest
from jinja2 import lexer as j2tokens
from jinja2.lexer import Lexer

from ansiblelint.jinja_utils.token import BEGIN_TOKENS, END_TOKENS, Tokens

from .jinja_fixtures import (
    CoreTagsFixtures,
    ExtendedAPIFixtures,
    ExtensionsFixtures,
    FilterFixtures,
    ImportsFixtures,
    IncludesFixtures,
    InheritanceFixtures,
    JinjaTestsFixtures,
    LexerFixtures,
    SyntaxFixtures,
    TrimBlocksFixtures,
)


@pytest.mark.parametrize(
    (
        "template_source",
        "jinja_token_count",
        "token_pairs_count",
        "expected_chomp_marks",
        "expected_chomps",
    ),
    (
        # spell-checker: disable
        (
            "{{ good_format }}\n{{- good_format }}\n{{- good_format -}}",
            9,
            3,
            ("-", "-", "-"),
            ("\n", "\n", ""),
        ),
        ("{{ [{'nested': ({'dict': [('tuple',), ()]}, {})}, {}] }}", 29, 10, (), ()),
        ("{{ ['slice', 'test', 1, 2, 3][1:3:-1] }}", 21, 3, (), ()),
        ("{{ ['slice', 'test', 1, 2, 3][2:] }}", 17, 3, (), ()),
        # these use fixtures from Jinja's test suite:
        (ExtendedAPIFixtures.item_and_attribute_1, 9, 2, (), ()),
        (ExtendedAPIFixtures.item_and_attribute_2, 12, 3, (), ()),
        (ExtendedAPIFixtures.item_and_attribute_3, 6, 2, (), ()),
        (CoreTagsFixtures.awaitable_property_slicing, 18, 4, (), ()),
        (CoreTagsFixtures.simple_for, 12, 3, (), ()),
        (CoreTagsFixtures.for_else, 14, 3, (), ()),
        (CoreTagsFixtures.for_else_scoping_item, 16, 5, (), ()),
        (CoreTagsFixtures.for_empty_blocks, 14, 3, (), ()),
        (CoreTagsFixtures.for_context_vars, 51, 9, ("-",), ("\n        ",)),
        (CoreTagsFixtures.for_cycling, 37, 8, (), ()),
        (
            CoreTagsFixtures.for_lookaround,
            35,
            7,
            ("-", "-"),
            (
                "\n            ",
                "\n        ",
            ),
        ),
        (
            CoreTagsFixtures.for_changed,
            18,
            4,
            ("-", "-"),
            ("\n            ", "\n        "),
        ),
        (CoreTagsFixtures.for_scope, 12, 3, (), ()),
        (CoreTagsFixtures.for_varlen, 12, 3, (), ()),
        (
            CoreTagsFixtures.for_recursive,
            36,
            7,
            ("-", "-"),
            ("\n            ", "\n        "),
        ),
        (
            CoreTagsFixtures.for_recursive_lookaround,
            68,
            9,
            ("-", "-"),
            ("\n            ", "\n        "),
        ),
        (
            CoreTagsFixtures.for_recursive_depth0,
            42,
            8,
            ("-", "-"),
            ("\n        ", "\n        "),
        ),
        (
            CoreTagsFixtures.for_recursive_depth,
            42,
            8,
            ("-", "-"),
            ("\n        ", "\n        "),
        ),
        (
            CoreTagsFixtures.for_looploop,
            37,
            7,
            ("-", "-", "-", "-", "-"),
            (
                # block rstrip \n
                "            ",
                "\n            ",
                "\n                ",
                "\n            ",
                # block rstrip \n
                "        ",
            ),
        ),
        (CoreTagsFixtures.for_reversed_bug, 23, 5, (), ()),
        (CoreTagsFixtures.for_loop_errors, 17, 5, (), ()),
        (CoreTagsFixtures.for_loop_filter_1, 21, 4, (), ()),
        (CoreTagsFixtures.for_loop_filter_2, 27, 5, ("-",), ("\n        ",)),
        (CoreTagsFixtures.for_scoped_special_var, 31, 6, (), ()),
        (CoreTagsFixtures.for_scoped_loop_var_1, 23, 5, (), ()),
        (CoreTagsFixtures.for_scoped_loop_var_2, 23, 5, (), ()),
        (
            CoreTagsFixtures.for_recursive_empty_loop_iter,
            10,
            2,
            ("-", "-", "-", "-"),
            ("\n        ", "", "", "\n        "),
        ),
        (
            CoreTagsFixtures.for_call_in_loop,
            43,
            12,
            ("-", "-", "-", "-", "-", "-", "-", "-", "-"),
            (
                "\n        ",
                "\n            ",
                "\n        ",
                # block rstrip \n
                "\n        ",
                # block rstrip \n
                "            ",
                "\n                ",
                "\n            ",
                # block rstrip \n
                "        ",
                "\n        ",
            ),
        ),
        (
            CoreTagsFixtures.for_scoping_bug,
            35,
            9,
            ("-", "-", "-", "-"),
            (
                "\n        ",
                # block rstrip \n
                "        ",
                # block rstrip \n
                "        ",
                "\n        ",
            ),
        ),
        (CoreTagsFixtures.for_unpacking, 32, 7, (), ()),
        (CoreTagsFixtures.for_intended_scoping_with_set_1, 21, 5, (), ()),
        (CoreTagsFixtures.for_intended_scoping_with_set_2, 27, 6, (), ()),
        (CoreTagsFixtures.simple_if, 8, 2, (), ()),
        (CoreTagsFixtures.if_elif, 17, 4, (), ()),
        (CoreTagsFixtures.if_elif_deep, 7007, 1002, (), ()),
        (CoreTagsFixtures.if_else, 12, 3, (), ()),
        (CoreTagsFixtures.if_empty, 12, 3, (), ()),
        (CoreTagsFixtures.if_complete, 24, 5, (), ()),
        (CoreTagsFixtures.if_no_scope_1, 16, 4, (), ()),
        (CoreTagsFixtures.if_no_scope_2, 16, 4, (), ()),
        (CoreTagsFixtures.simple_macros, 21, 6, (), ()),
        (CoreTagsFixtures.macros_scoping, 39, 12, (), ()),
        (CoreTagsFixtures.macros_arguments, 67, 15, (), ()),
        (CoreTagsFixtures.macros_varargs, 27, 7, (), ()),
        (CoreTagsFixtures.macros_simple_call, 26, 8, (), ()),
        (CoreTagsFixtures.macros_complex_call, 32, 10, (), ()),
        (CoreTagsFixtures.macros_caller_undefined, 26, 7, (), ()),
        (CoreTagsFixtures.macros_include, 12, 3, (), ()),
        (CoreTagsFixtures.macros_macro_api, 41, 13, (), ()),
        (CoreTagsFixtures.macros_callself, 37, 10, (), ()),
        (
            CoreTagsFixtures.macros_macro_defaults_self_ref,
            35,
            7,
            ("-", "-", "-"),
            (
                "\n        ",
                # block rstrip \n
                "        ",
                "\n    ",
            ),
        ),
        (CoreTagsFixtures.set_normal, 9, 2, (), ()),
        (CoreTagsFixtures.set_block, 11, 3, (), ()),
        (CoreTagsFixtures.set_block_escaping, 16, 4, (), ()),
        (CoreTagsFixtures.set_namespace, 21, 4, (), ()),
        (CoreTagsFixtures.set_namespace_block, 23, 5, (), ()),
        (CoreTagsFixtures.set_init_namespace, 38, 6, (), ()),
        (CoreTagsFixtures.set_namespace_loop, 45, 9, (), ()),
        (CoreTagsFixtures.set_namespace_macro, 51, 11, (), ()),
        (CoreTagsFixtures.set_block_escaping_filtered, 18, 4, (), ()),
        (CoreTagsFixtures.set_block_filtered, 17, 3, (), ()),
        (
            CoreTagsFixtures.with_with,
            30,
            6,
            ("-", "-"),
            ("\n            ", "\n            "),
        ),
        (
            CoreTagsFixtures.with_with_argument_scoping,
            44,
            7,
            ("-", "-", "-", "-"),
            ("        ", "\n            ", "\n        ", "\n        "),
        ),
        (FilterFixtures.capitalize, 5, 1, (), ()),
        (FilterFixtures.center, 8, 2, (), ()),
        (FilterFixtures.default, 37, 8, (), ()),
        (FilterFixtures.dictsort_1, 7, 2, (), ()),
        (FilterFixtures.dictsort_2, 8, 2, (), ()),
        (FilterFixtures.dictsort_3, 10, 2, (), ()),
        (FilterFixtures.dictsort_4, 10, 2, (), ()),
        (FilterFixtures.batch, 23, 4, (), ()),
        (FilterFixtures.slice_, 23, 4, (), ()),
        (FilterFixtures.escape, 5, 1, (), ()),
        (FilterFixtures.trim, 8, 2, (), ()),
        (FilterFixtures.striptags, 5, 1, (), ()),
        (FilterFixtures.filesizeformat, 74, 15, (), ()),
        (FilterFixtures.filesizeformat_issue59, 56, 11, (), ()),
        (FilterFixtures.first, 5, 1, (), ()),
        (FilterFixtures.float_, 5, 1, (), ()),
        (FilterFixtures.float_default, 10, 2, (), ()),
        (FilterFixtures.format_, 10, 2, (), ()),
        (FilterFixtures.indent_1, 12, 2, (), ()),
        (FilterFixtures.indent_2, 12, 2, (), ()),
        (FilterFixtures.indent_3, 12, 2, (), ()),
        (FilterFixtures.indent_4, 12, 2, (), ()),
        (FilterFixtures.indent_5, 5, 1, (), ()),
        (FilterFixtures.indent_6, 10, 2, (), ()),
        (FilterFixtures.indent_7, 10, 2, (), ()),
        (FilterFixtures.indent_width_string, 14, 2, (), ()),
        (FilterFixtures.int_, 5, 1, (), ()),
        (FilterFixtures.int_base, 10, 2, (), ()),
        (FilterFixtures.int_default, 10, 2, (), ()),
        (FilterFixtures.join_1, 14, 3, (), ()),
        (FilterFixtures.join_2, 11, 2, (), ()),
        (FilterFixtures.join_attribute, 10, 2, (), ()),
        (FilterFixtures.last, 5, 1, (), ()),
        (FilterFixtures.length, 5, 1, (), ()),
        (FilterFixtures.lower, 5, 1, (), ()),
        (FilterFixtures.items, 7, 1, (), ()),
        (FilterFixtures.items_undefined, 7, 1, (), ()),
        (FilterFixtures.pprint, 5, 1, (), ()),
        (FilterFixtures.random, 5, 1, (), ()),
        (FilterFixtures.reverse, 21, 3, (), ()),
        (FilterFixtures.string, 5, 1, (), ()),
        (FilterFixtures.title_1, 5, 1, (), ()),
        (FilterFixtures.title_2, 5, 1, (), ()),
        (FilterFixtures.title_3, 5, 1, (), ()),
        (FilterFixtures.title_4, 5, 1, (), ()),
        (FilterFixtures.title_5, 5, 1, (), ()),
        (FilterFixtures.title_6, 5, 1, (), ()),
        (FilterFixtures.title_7, 5, 1, (), ()),
        (FilterFixtures.title_8, 5, 1, (), ()),
        (FilterFixtures.title_9, 5, 1, (), ()),
        (FilterFixtures.title_10, 5, 1, (), ()),
        (FilterFixtures.title_11, 5, 1, (), ()),
        (FilterFixtures.title_12, 5, 1, (), ()),
        (FilterFixtures.truncate, 34, 6, (), ()),
        (FilterFixtures.truncate_very_short, 19, 4, (), ()),
        (FilterFixtures.truncate_end_length, 10, 2, (), ()),
        (FilterFixtures.upper, 5, 1, (), ()),
        (FilterFixtures.urlize_1, 5, 1, (), ()),
        (FilterFixtures.urlize_2, 5, 1, (), ()),
        (FilterFixtures.urlize_3, 5, 1, (), ()),
        (FilterFixtures.urlize_4, 5, 1, (), ()),
        (FilterFixtures.urlize_rel_policy, 5, 1, (), ()),
        (FilterFixtures.urlize_target_parameters, 10, 2, (), ()),
        (FilterFixtures.urlize_extra_schemes_parameters, 14, 3, (), ()),
        (FilterFixtures.wordcount_1, 5, 1, (), ()),
        (FilterFixtures.wordcount_2, 5, 1, (), ()),
        (FilterFixtures.block, 10, 2, (), ()),
        (FilterFixtures.chaining, 13, 2, (), ()),
        (FilterFixtures.sum_, 17, 2, (), ()),
        (FilterFixtures.sum_attributes, 8, 2, (), ()),
        (FilterFixtures.sum_attributes_nested, 8, 2, (), ()),
        (FilterFixtures.sum_attributes_tuple, 12, 3, (), ()),
        (FilterFixtures.abs_, 12, 2, (), ()),
        (FilterFixtures.round_positive, 33, 6, (), ()),
        (FilterFixtures.round_negative, 33, 6, (), ()),
        (FilterFixtures.xmlattr, 25, 2, (), ()),
        (FilterFixtures.sort1, 26, 5, (), ()),
        (FilterFixtures.sort2, 18, 3, (), ()),
        (FilterFixtures.sort3, 11, 2, (), ()),
        (FilterFixtures.sort4, 12, 2, (), ()),
        (FilterFixtures.sort5, 12, 2, (), ()),
        (FilterFixtures.sort6, 12, 2, (), ()),
        (FilterFixtures.sort7, 12, 2, (), ()),
        (FilterFixtures.sort8, 12, 2, (), ()),
        (FilterFixtures.unique, 18, 3, (), ()),
        (FilterFixtures.unique_case_sensitive, 21, 4, (), ()),
        (FilterFixtures.unique_attribute, 12, 2, (), ()),
        (FilterFixtures.min_1, 9, 2, (), ()),
        (FilterFixtures.min_2, 14, 3, (), ()),
        (FilterFixtures.min_3, 6, 2, (), ()),
        (FilterFixtures.max_1, 9, 2, (), ()),
        (FilterFixtures.max_2, 14, 3, (), ()),
        (FilterFixtures.max_3, 6, 2, (), ()),
        (FilterFixtures.min_attribute, 10, 2, (), ()),
        (FilterFixtures.max_attribute, 10, 2, (), ()),
        (
            FilterFixtures.groupby,
            81,
            13,
            ("-", "-", "-"),
            ("\n        ", "\n            ", "\n        "),
        ),
        (
            FilterFixtures.groupby_tuple_index,
            53,
            11,
            ("-", "-", "-"),
            ("\n        ", "\n            ", "\n        "),
        ),
        (
            FilterFixtures.groupby_multi_dot,
            36,
            7,
            ("-", "-", "-"),
            ("\n        ", "\n            ", "\n        "),
        ),
        (FilterFixtures.groupby_default, 40, 7, (), ()),
        (FilterFixtures.groupby_case, 37, 6, (), ()),
        (FilterFixtures.filter_tag, 15, 3, (), ()),
        (FilterFixtures.replace_1, 10, 2, (), ()),
        (FilterFixtures.replace_2, 10, 2, (), ()),
        (FilterFixtures.replace_3, 10, 2, (), ()),
        (FilterFixtures.forceescape, 5, 1, (), ()),
        (FilterFixtures.safe_1, 5, 1, (), ()),
        (FilterFixtures.safe_2, 3, 1, (), ()),
        (FilterFixtures.urlencode, 5, 1, (), ()),
        (FilterFixtures.simple_map, 16, 3, (), ()),
        (FilterFixtures.map_sum, 28, 6, (), ()),
        (FilterFixtures.attribute_map, 15, 3, (), ()),
        (FilterFixtures.empty_map, 10, 2, (), ()),
        (FilterFixtures.map_default, 19, 3, (), ()),
        (FilterFixtures.map_default_list, 23, 4, (), ()),
        (FilterFixtures.map_default_str, 19, 3, (), ()),
        (FilterFixtures.simple_select, 23, 4, (), ()),
        (FilterFixtures.bool_select, 26, 3, (), ()),
        (FilterFixtures.simple_reject, 23, 4, (), ()),
        (FilterFixtures.bool_reject, 26, 3, (), ()),
        (FilterFixtures.simple_select_attr, 20, 4, (), ()),
        (FilterFixtures.simple_reject_attr, 20, 4, (), ()),
        (FilterFixtures.func_select_attr, 22, 4, (), ()),
        (FilterFixtures.func_reject_attr, 22, 4, (), ()),
        (FilterFixtures.json_dump, 5, 1, (), ()),
        (FilterFixtures.wordwrap, 8, 2, (), ()),
        (FilterFixtures.filter_undefined, 5, 1, (), ()),
        (
            FilterFixtures.filter_undefined_in_if,
            18,
            4,
            ("-", "-", "-", "-"),
            ("", "", "", ""),
        ),
        (
            FilterFixtures.filter_undefined_in_elif,
            27,
            6,
            ("-", "-", "-", "-", "-", "-", "-", "-"),
            ("", "", "", "", "", "", "", ""),
        ),
        (
            FilterFixtures.filter_undefined_in_else,
            19,
            4,
            ("-", "-", "-", "-", "-", "-"),
            ("", "", "", "", "", ""),
        ),
        (
            FilterFixtures.filter_undefined_in_nested_if,
            31,
            7,
            ("-", "-", "-", "-", "-", "-", "-", "-", "-", "-"),
            ("", "", "", "", "", "", "", "", "", ""),
        ),
        (FilterFixtures.filter_undefined_in_condexpr_1, 11, 1, (), ()),
        (FilterFixtures.filter_undefined_in_condexpr_2, 12, 1, (), ()),
        (TrimBlocksFixtures.trim, 9, 2, (), ()),
        (TrimBlocksFixtures.no_trim, 9, 2, ("+",), ()),
        (TrimBlocksFixtures.no_trim_outer, 9, 2, ("+",), ()),
        (TrimBlocksFixtures.lstrip_no_trim, 9, 2, ("+",), ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_block1, 9, 2, (), ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_block2, 9, 2, ("+",), ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_comment1, 2, 1, (), ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_comment2, 2, 1, ("+",), ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_raw1, 2, 1, (), ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_raw2, 2, 1, ("+",), ()),
        (TrimBlocksFixtures.trim_nested, 18, 4, (), ()),
        (TrimBlocksFixtures.no_trim_nested, 18, 4, ("+", "+", "+"), ()),
        (TrimBlocksFixtures.comment_trim, 2, 1, (), ()),
        (TrimBlocksFixtures.comment_no_trim, 2, 1, ("+",), ()),
        (TrimBlocksFixtures.multiple_comment_trim_lstrip, 4, 3, (), ()),
        (TrimBlocksFixtures.multiple_comment_no_trim_lstrip, 4, 3, ("+", "+", "+"), ()),
        (TrimBlocksFixtures.raw_trim_lstrip, 8, 3, (), ()),
        (TrimBlocksFixtures.raw_no_trim_lstrip, 8, 3, ("+",), ()),
        (ImportsFixtures.context_imports_1, 13, 3, (), ()),
        (ImportsFixtures.context_imports_2, 15, 3, (), ()),
        (ImportsFixtures.context_imports_3, 15, 3, (), ()),
        (ImportsFixtures.context_imports_4, 11, 3, (), ()),
        (ImportsFixtures.context_imports_5, 13, 3, (), ()),
        (ImportsFixtures.context_imports_6, 13, 3, (), ()),
        (ImportsFixtures.import_needs_name_1, 6, 1, (), ()),
        (ImportsFixtures.import_needs_name_2, 8, 1, (), ()),
        (ImportsFixtures.trailing_comma_with_context_1, 10, 1, (), ()),
        (ImportsFixtures.trailing_comma_with_context_2, 11, 1, (), ()),
        (ImportsFixtures.trailing_comma_with_context_3, 9, 1, (), ()),
        (ImportsFixtures.trailing_comma_with_context_4, 10, 1, (), ()),
        (ImportsFixtures.trailing_comma_with_context_5, 10, 1, (), ()),
        (ImportsFixtures.exports, 53, 13, (), ()),
        (ImportsFixtures.import_with_globals, 13, 3, (), ()),
        (ImportsFixtures.import_with_globals_override, 19, 4, (), ()),
        (ImportsFixtures.from_import_with_globals, 11, 3, (), ()),
        (IncludesFixtures.context_include_1, 4, 1, (), ()),
        (IncludesFixtures.context_include_2, 6, 1, (), ()),
        (IncludesFixtures.context_include_3, 6, 1, (), ()),
        (IncludesFixtures.choice_includes_1, 8, 2, (), ()),
        (IncludesFixtures.choice_includes_2, 10, 2, (), ()),
        (IncludesFixtures.choice_includes_4, 8, 2, (), ()),
        (IncludesFixtures.choice_includes_5, 4, 1, (), ()),
        (IncludesFixtures.choice_includes_6, 8, 2, (), ()),
        (IncludesFixtures.choice_includes_7, 4, 1, (), ()),
        (IncludesFixtures.choice_includes_8, 6, 2, (), ()),
        (IncludesFixtures.include_ignoring_missing_2, 6, 1, (), ()),
        (IncludesFixtures.include_ignoring_missing_3, 8, 1, (), ()),
        (IncludesFixtures.include_ignoring_missing_4, 8, 1, (), ()),
        (IncludesFixtures.context_include_with_overrides_main, 19, 4, (), ()),
        (IncludesFixtures.context_include_with_overrides_item, 3, 1, (), ()),
        (IncludesFixtures.unoptimized_scopes, 42, 11, (), ()),
        (IncludesFixtures.import_from_with_context_a, 12, 4, (), ()),
        (IncludesFixtures.import_from_with_context, 19, 4, (), ()),
        (InheritanceFixtures.layout, 35, 8, (), ()),
        (InheritanceFixtures.level1, 12, 3, (), ()),
        (InheritanceFixtures.level2, 19, 5, (), ()),
        (InheritanceFixtures.level3, 20, 5, (), ()),
        (InheritanceFixtures.level4, 12, 3, (), ()),
        (InheritanceFixtures.working, 29, 7, (), ()),
        (InheritanceFixtures.double_e, 33, 8, (), ()),
        (InheritanceFixtures.super_a, 18, 4, (), ()),
        (InheritanceFixtures.super_b, 18, 5, (), ()),
        (InheritanceFixtures.super_c, 32, 9, (), ()),
        (InheritanceFixtures.reuse_blocks, 24, 6, (), ()),
        (InheritanceFixtures.preserve_blocks_a, 22, 6, (), ()),
        (InheritanceFixtures.preserve_blocks_b, 17, 5, (), ()),
        (InheritanceFixtures.dynamic_inheritance_default1, 8, 2, (), ()),
        (InheritanceFixtures.dynamic_inheritance_default2, 8, 2, (), ()),
        (InheritanceFixtures.dynamic_inheritance_child, 12, 3, (), ()),
        (InheritanceFixtures.multi_inheritance_default1, 8, 2, (), ()),
        (InheritanceFixtures.multi_inheritance_default2, 8, 2, (), ()),
        (InheritanceFixtures.multi_inheritance_child, 26, 7, (), ()),
        (InheritanceFixtures.scoped_block_default_html, 19, 4, (), ()),
        (InheritanceFixtures.scoped_block, 14, 4, (), ()),
        (InheritanceFixtures.super_in_scoped_block_default_html, 22, 5, (), ()),
        (InheritanceFixtures.super_in_scoped_block, 22, 6, (), ()),
        (InheritanceFixtures.scoped_block_after_inheritance_layout_html, 9, 2, (), ()),
        (
            InheritanceFixtures.scoped_block_after_inheritance_index_html,
            57,
            11,
            ("-",),
            ("\n        ",),
        ),
        (
            InheritanceFixtures.scoped_block_after_inheritance_helpers_html,
            17,
            4,
            (),
            (),
        ),
        (InheritanceFixtures.level1_required_default, 9, 3, (), ()),
        (InheritanceFixtures.level1_required_level1, 12, 3, (), ()),
        (InheritanceFixtures.level2_required_default, 8, 2, (), ()),
        (InheritanceFixtures.level2_required_level1, 12, 3, (), ()),
        (InheritanceFixtures.level2_required_level2, 12, 3, (), ()),
        (InheritanceFixtures.level3_required_default, 8, 2, (), ()),
        (InheritanceFixtures.level3_required_level1, 4, 1, (), ()),
        (InheritanceFixtures.level3_required_level2, 12, 3, (), ()),
        (InheritanceFixtures.level3_required_level3, 4, 1, (), ()),
        (InheritanceFixtures.required_with_scope_default1, 20, 4, (), ()),
        (InheritanceFixtures.required_with_scope_child1, 14, 4, (), ()),
        (ExtensionsFixtures.extend_late, 10, 3, (), ()),
        (
            ExtensionsFixtures.loop_controls_1,
            34,
            7,
            ("-", "-", "-", "-"),
            (
                "\n        ",
                # block rstrip \n
                "            ",
                "\n            ",
                "\n        ",
            ),
        ),
        (
            ExtensionsFixtures.loop_controls_2,
            32,
            7,
            ("-", "-", "-", "-"),
            (
                "\n        ",
                # block rstrip \n
                "            ",
                "\n            ",
                "\n        ",
            ),
        ),
        (
            ExtensionsFixtures.do,
            37,
            8,
            ("-", "-", "-", "-"),
            (
                "\n        ",
                # block rstrip \n
                "        ",
                # block rstrip \n
                "            ",
                # block rstrip \n
                "        ",
            ),
        ),
        (ExtensionsFixtures.extension_nodes, 3, 1, (), ()),
        (ExtensionsFixtures.contextreference_node_passes_context, 9, 2, (), ()),
        (ExtensionsFixtures.contextreference_node_can_pass_locals, 14, 4, (), ()),
        # (ExtensionsFixtures.preprocessor_extension, 1, 0, (), ()),  # odd
        # (ExtensionsFixtures.streamfilter_extension, 1, 0, (), ()),  # odd
        (ExtensionsFixtures.debug, 5, 1, (), ()),
        (
            ExtensionsFixtures.scope,
            44,
            7,
            ("-", "-", "-", "-"),
            ("        ", "\n            ", "\n        ", "\n        "),
        ),
        (ExtensionsFixtures.auto_escape_scoped_setting_1, 22, 5, (), ()),
        (ExtensionsFixtures.auto_escape_scoped_setting_2, 22, 5, (), ()),
        (ExtensionsFixtures.auto_escape_nonvolatile_1, 11, 2, (), ()),
        (ExtensionsFixtures.auto_escape_nonvolatile_2, 18, 4, (), ()),
        (ExtensionsFixtures.auto_escape_volatile, 18, 4, (), ()),
        (ExtensionsFixtures.auto_escape_scoping, 22, 6, (), ()),
        (ExtensionsFixtures.auto_escape_volatile_scoping, 40, 9, (), ()),
        (
            ExtensionsFixtures.auto_escape_overlay_scopes,
            42,
            10,
            ("-", "-", "-", "-", "-", "-"),
            (
                "\n        ",
                # block rstrip \n
                "        ",
                # block rstrip \n
                "            ",
                # block rstrip \n
                "        ",
                "\n        ",
                "\n        ",
            ),
        ),
        (LexerFixtures.raw1, 3, 2, (), ()),
        (
            LexerFixtures.raw2,
            3,
            1,
            ("-", "-"),
            # unlike other tags, raw consumes {% and %} in a single token.
            ("  {%- raw -%}   ", "   {%- endraw -%}   "),
        ),
        (LexerFixtures.raw3, 3, 1, (), ()),
        (
            LexerFixtures.raw4,
            3,
            1,
            ("-", "-"),
            # unlike other tags, raw consumes {% and %} in a single token.
            ("\n{%- raw -%}\n\n  \n  ", "{%- endraw -%}\n"),
        ),
        (LexerFixtures.bytefallback, 11, 2, (), ()),
        (LexerFixtures.lineno_with_strip, 14, 3, ("-", "-"), ("\n    ", "\n        ")),
        (LexerFixtures.start_comment, 15, 6, (), ()),
        (SyntaxFixtures.slicing, 28, 6, (), ()),
        (SyntaxFixtures.attr, 12, 3, (), ()),
        (SyntaxFixtures.subscript, 14, 4, (), ()),
        (SyntaxFixtures.tuple_, 19, 6, (), ()),
        (SyntaxFixtures.math, 19, 3, (), ()),
        (SyntaxFixtures.div, 17, 3, (), ()),
        (SyntaxFixtures.unary, 9, 2, (), ()),
        (SyntaxFixtures.concat, 9, 2, (), ()),
        (SyntaxFixtures.compare_1, 5, 1, (), ()),
        (SyntaxFixtures.compare_2, 5, 1, (), ()),
        (SyntaxFixtures.compare_3, 5, 1, (), ()),
        (SyntaxFixtures.compare_4, 5, 1, (), ()),
        (SyntaxFixtures.compare_5, 5, 1, (), ()),
        (SyntaxFixtures.compare_6, 5, 1, (), ()),
        (SyntaxFixtures.compare_parens, 9, 2, (), ()),
        (SyntaxFixtures.compare_compound_1, 7, 1, (), ()),
        (SyntaxFixtures.compare_compound_2, 7, 1, (), ()),
        (SyntaxFixtures.compare_compound_3, 7, 1, (), ()),
        (SyntaxFixtures.compare_compound_4, 7, 1, (), ()),
        (SyntaxFixtures.compare_compound_5, 7, 1, (), ()),
        (SyntaxFixtures.compare_compound_6, 7, 1, (), ()),
        (SyntaxFixtures.inop, 24, 4, (), ()),
        (SyntaxFixtures.collection_literal_1, 4, 2, (), ()),
        (SyntaxFixtures.collection_literal_2, 4, 2, (), ()),
        (SyntaxFixtures.collection_literal_3, 4, 2, (), ()),
        (SyntaxFixtures.numeric_literal_1, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_2, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_3, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_4, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_5, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_6, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_7, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_8, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_9, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_10, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_11, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_12, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_13, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_14, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_15, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_16, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_17, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_18, 3, 1, (), ()),
        (SyntaxFixtures.numeric_literal_19, 3, 1, (), ()),
        (SyntaxFixtures.boolean, 16, 3, (), ()),
        (SyntaxFixtures.grouping, 16, 3, (), ()),
        (SyntaxFixtures.django_attr, 23, 5, (), ()),
        (SyntaxFixtures.conditional_expression, 7, 1, (), ()),
        (SyntaxFixtures.short_conditional_expression, 7, 1, (), ()),
        (SyntaxFixtures.filter_priority, 9, 1, (), ()),
        (SyntaxFixtures.function_calls_1, 8, 2, (), ()),
        (SyntaxFixtures.function_calls_2, 10, 2, (), ()),
        (SyntaxFixtures.function_calls_3, 13, 2, (), ()),
        (SyntaxFixtures.function_calls_4, 13, 2, (), ()),
        (SyntaxFixtures.function_calls_5, 16, 2, (), ()),
        (SyntaxFixtures.function_calls_6, 11, 2, (), ()),
        (SyntaxFixtures.function_calls_7, 10, 2, (), ()),
        (SyntaxFixtures.function_calls_8, 14, 2, (), ()),
        (SyntaxFixtures.function_calls_9, 16, 2, (), ()),
        (SyntaxFixtures.tuple_expr_1, 4, 2, (), ()),
        (SyntaxFixtures.tuple_expr_2, 7, 2, (), ()),
        (SyntaxFixtures.tuple_expr_3, 8, 2, (), ()),
        (SyntaxFixtures.tuple_expr_4, 4, 1, (), ()),
        (SyntaxFixtures.tuple_expr_5, 5, 1, (), ()),
        (SyntaxFixtures.tuple_expr_6, 12, 2, (), ()),
        (SyntaxFixtures.tuple_expr_7, 12, 2, (), ()),
        (SyntaxFixtures.tuple_expr_8, 11, 2, (), ()),
        (SyntaxFixtures.trailing_comma, 26, 6, (), ()),
        (SyntaxFixtures.block_end_name, 9, 2, (), ()),
        (SyntaxFixtures.constant_casing_true, 11, 3, (), ()),
        (SyntaxFixtures.constant_casing_false, 11, 3, (), ()),
        (SyntaxFixtures.constant_casing_none, 11, 3, (), ()),
        (SyntaxFixtures.chaining_tests, 9, 1, (), ()),
        (SyntaxFixtures.string_concatenation, 5, 1, (), ()),
        (SyntaxFixtures.not_in, 6, 1, (), ()),
        (SyntaxFixtures.operator_precedence, 13, 1, (), ()),
        (SyntaxFixtures.raw2, 1, 1, (), ()),
        (SyntaxFixtures.const, 23, 5, (), ()),
        (SyntaxFixtures.neg_filter_priority, 6, 1, (), ()),
        (SyntaxFixtures.localset, 28, 6, (), ()),
        (SyntaxFixtures.parse_unary_1, 7, 2, (), ()),
        (SyntaxFixtures.parse_unary_2, 9, 2, (), ()),
        (JinjaTestsFixtures.defined, 11, 2, (), ()),
        (JinjaTestsFixtures.even, 11, 2, (), ()),
        (JinjaTestsFixtures.odd, 11, 2, (), ()),
        (JinjaTestsFixtures.lower, 11, 2, (), ()),
        (JinjaTestsFixtures.upper, 11, 2, (), ()),
        (JinjaTestsFixtures.equalto, 63, 10, (), ()),
        (JinjaTestsFixtures.sameas, 13, 2, (), ()),
        (JinjaTestsFixtures.no_paren_for_arg1, 6, 1, (), ()),
        (JinjaTestsFixtures.escaped, 11, 2, (), ()),
        (JinjaTestsFixtures.greaterthan, 13, 2, (), ()),
        (JinjaTestsFixtures.lessthan, 13, 2, (), ()),
        (JinjaTestsFixtures.multiple_tests, 11, 1, (), ()),
        (JinjaTestsFixtures.in_, 90, 17, (), ()),
        (JinjaTestsFixtures.name_undefined, 5, 1, (), ()),
        (JinjaTestsFixtures.name_undefined_in_if, 14, 3, (), ()),
    )
    + tuple(
        ("{{ " + alias_test[0] + " }}", 6, 1, (), ())
        for alias_test in JinjaTestsFixtures.compare_aliases
    ),
    # spell-checker: enable
)
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def test_tokens_iterator(  # noqa: C901  # splitting this up would hurt readability
    lexer: Lexer,
    template_source: str,
    jinja_token_count: int,
    token_pairs_count: int,
    expected_chomp_marks: tuple[Literal["+", "-"], ...],
    expected_chomps: tuple[str, ...],
) -> None:
    """Validate sanity of iterating over wrapped-lexed tokens in Token."""
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
        if i == last_index:
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
            if (
                token.token == j2tokens.TOKEN_OPERATOR
                # convince mypy that jinja_token is never None w/ operator tokens:
                and token.jinja_token is not None
                and token.jinja_token.type
                in (
                    j2tokens.TOKEN_LBRACKET,
                    j2tokens.TOKEN_RBRACKET,
                    j2tokens.TOKEN_LBRACE,
                    j2tokens.TOKEN_RBRACE,
                    j2tokens.TOKEN_LPAREN,
                    j2tokens.TOKEN_RPAREN,
                )
            ):
                assert token.jinja_token is not None  # is None for comment tokens
                assert token.pair.jinja_token is not None  # is None for comment tokens
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

    chomp_marks = tuple(t.chomp for t in tokens if t.chomp)
    assert chomp_marks == expected_chomp_marks
    chomps = tuple(
        t.value_str.rstrip("{%-")
        if t.token in BEGIN_TOKENS
        else t.value_str.lstrip("-%}")
        for t in tokens
        if t.chomp == "-"
    )
    assert chomps == expected_chomps