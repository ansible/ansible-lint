from typing import Literal, Tuple

import pytest
from ansible.template import Templar
from jinja2 import lexer as j2tokens
from jinja2.lexer import Lexer

from ansiblelint.jinja_utils.token import BEGIN_TOKENS, END_TOKENS, Tokens
from ansiblelint.utils import ansible_templar

from .jinja_fixtures import CoreTagsFixtures, FilterFixtures, TrimBlocksFixtures


@pytest.fixture
def templar() -> Templar:
    basedir = "/base/dir"
    templatevars = {"playbook_dir": "/a/b/c"}
    return ansible_templar(basedir, templatevars)


@pytest.fixture
def lexer(templar: Templar) -> Lexer:
    return templar.environment.lexer


@pytest.mark.parametrize(
    ("template_source", "jinja_token_count", "token_pairs_count", "expected_chomps"),
    (
        # jinja_token_count is the number of tokens + 2 (INITIAL, and EOF)
        ("{{ [{'nested': ({'dict': [('tuple',), ()]}, {})}, {}] }}", 31, 10, ()),
        # these use fixtures from Jinja's test suite:
        (CoreTagsFixtures.simple_for, 14, 3, ()),
        (CoreTagsFixtures.for_else, 16, 3, ()),
        (CoreTagsFixtures.for_else_scoping_item, 18, 5, ()),
        (CoreTagsFixtures.for_empty_blocks, 16, 3, ()),
        (CoreTagsFixtures.for_context_vars, 53, 9, ("-",)),
        (CoreTagsFixtures.for_cycling, 39, 8, ()),
        (CoreTagsFixtures.for_lookaround, 37, 7, ("-", "-")),
        (CoreTagsFixtures.for_changed, 20, 4, ("-", "-")),
        (CoreTagsFixtures.for_scope, 14, 3, ()),
        (CoreTagsFixtures.for_varlen, 14, 3, ()),
        (CoreTagsFixtures.for_recursive, 38, 7, ("-", "-")),
        (CoreTagsFixtures.for_recursive_lookaround, 70, 9, ("-", "-")),
        (CoreTagsFixtures.for_recursive_depth0, 44, 8, ("-", "-")),
        (CoreTagsFixtures.for_recursive_depth, 44, 8, ("-", "-")),
        (CoreTagsFixtures.for_looploop, 39, 7, ("-", "-", "-", "-", "-")),
        (CoreTagsFixtures.for_reversed_bug, 25, 5, ()),
        (CoreTagsFixtures.for_loop_errors, 19, 5, ()),
        (CoreTagsFixtures.for_loop_filter_1, 23, 4, ()),
        (CoreTagsFixtures.for_loop_filter_2, 29, 5, ("-",)),
        (CoreTagsFixtures.for_scoped_special_var, 33, 6, ()),
        (CoreTagsFixtures.for_scoped_loop_var_1, 25, 5, ()),
        (CoreTagsFixtures.for_scoped_loop_var_2, 25, 5, ()),
        (CoreTagsFixtures.for_recursive_empty_loop_iter, 12, 2, ("-", "-", "-", "-")),
        (
            CoreTagsFixtures.for_call_in_loop,
            45,
            12,
            ("-", "-", "-", "-", "-", "-", "-", "-", "-"),
        ),
        (CoreTagsFixtures.for_scoping_bug, 37, 9, ("-", "-", "-", "-")),
        (CoreTagsFixtures.for_unpacking, 34, 7, ()),
        (CoreTagsFixtures.for_intended_scoping_with_set_1, 23, 5, ()),
        (CoreTagsFixtures.for_intended_scoping_with_set_2, 29, 6, ()),
        (CoreTagsFixtures.simple_if, 10, 2, ()),
        (CoreTagsFixtures.if_elif, 19, 4, ()),
        (CoreTagsFixtures.if_elif_deep, 7009, 1002, ()),
        (CoreTagsFixtures.if_else, 14, 3, ()),
        (CoreTagsFixtures.if_empty, 14, 3, ()),
        (CoreTagsFixtures.if_complete, 26, 5, ()),
        (CoreTagsFixtures.if_no_scope_1, 18, 4, ()),
        (CoreTagsFixtures.if_no_scope_2, 18, 4, ()),
        (CoreTagsFixtures.simple_macros, 23, 6, ()),
        (CoreTagsFixtures.macros_scoping, 41, 12, ()),
        (CoreTagsFixtures.macros_arguments, 69, 15, ()),
        (CoreTagsFixtures.macros_varargs, 29, 7, ()),
        (CoreTagsFixtures.macros_simple_call, 28, 8, ()),
        (CoreTagsFixtures.macros_complex_call, 34, 10, ()),
        (CoreTagsFixtures.macros_caller_undefined, 28, 7, ()),
        (CoreTagsFixtures.macros_include, 14, 3, ()),
        (CoreTagsFixtures.macros_macro_api, 43, 13, ()),
        (CoreTagsFixtures.macros_callself, 39, 10, ()),
        (CoreTagsFixtures.macros_macro_defaults_self_ref, 37, 7, ("-", "-", "-")),
        (CoreTagsFixtures.set_normal, 11, 2, ()),
        (CoreTagsFixtures.set_block, 13, 3, ()),
        (CoreTagsFixtures.set_block_escaping, 18, 4, ()),
        (CoreTagsFixtures.set_namespace, 23, 4, ()),
        (CoreTagsFixtures.set_namespace_block, 25, 5, ()),
        (CoreTagsFixtures.set_init_namespace, 40, 6, ()),
        (CoreTagsFixtures.set_namespace_loop, 47, 9, ()),
        (CoreTagsFixtures.set_namespace_macro, 53, 11, ()),
        (CoreTagsFixtures.set_block_escaping_filtered, 20, 4, ()),
        (CoreTagsFixtures.set_block_filtered, 19, 3, ()),
        (CoreTagsFixtures.with_with, 32, 6, ("-", "-")),
        (CoreTagsFixtures.with_with_argument_scoping, 46, 7, ("-", "-", "-", "-")),
        (FilterFixtures.groupby, 83, 13, ("-", "-", "-")),
        (FilterFixtures.groupby_tuple_index, 55, 11, ("-", "-", "-")),
        (TrimBlocksFixtures.trim, 11, 2, ()),
        (TrimBlocksFixtures.no_trim, 11, 2, ("+",)),
        (TrimBlocksFixtures.no_trim_outer, 11, 2, ("+",)),
        (TrimBlocksFixtures.lstrip_no_trim, 11, 2, ("+",)),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_block1, 11, 2, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_block2, 11, 2, ("+",)),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_comment1, 4, 1, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_comment2, 4, 1, ("+",)),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_raw1, 4, 1, ()),
        (TrimBlocksFixtures.trim_blocks_false_with_no_trim_raw2, 4, 1, ("+",)),
        (TrimBlocksFixtures.trim_nested, 20, 4, ()),
        (TrimBlocksFixtures.no_trim_nested, 20, 4, ("+", "+", "+")),
        (TrimBlocksFixtures.comment_trim, 4, 1, ()),
        (TrimBlocksFixtures.comment_no_trim, 4, 1, ("+",)),
        (TrimBlocksFixtures.multiple_comment_trim_lstrip, 6, 3, ()),
        (TrimBlocksFixtures.multiple_comment_no_trim_lstrip, 6, 3, ("+", "+", "+")),
        (TrimBlocksFixtures.raw_trim_lstrip, 10, 3, ()),
        (TrimBlocksFixtures.raw_no_trim_lstrip, 10, 3, ("+",)),
        # ^^ 79 tests
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
