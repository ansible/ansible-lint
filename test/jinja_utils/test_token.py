from typing import Literal, Tuple

import pytest

from ansible.template import Templar
from jinja2.lexer import Lexer

from ansiblelint.utils import ansible_templar
from ansiblelint.jinja_utils.token import Token, tokeniter


@pytest.fixture
def templar() -> Templar:
    basedir = "/base/dir"
    templatevars = {"playbook_dir": "/a/b/c"}
    return ansible_templar(basedir, templatevars)


@pytest.fixture
def lexer(templar: Templar) -> Lexer:
    return templar.environment.lexer


@pytest.mark.parametrize(
    ("template_source", "jinja_tokens_count", "token_pairs_count", "expected_chomps"),
    (
        (
            src,
            0,
            0,
            (),
        ),
    ),
)
def test_tokeniter(
    lexer: Lexer,
    template_source: src,
    jinja_token_count: int,
    token_pairs_count: int,
    expected_chomps: Tuple[Literal["+", "-"], ...],
):
    tokens = [t for t in tokeniter(lexer, template_source)]
    tokens_count = len(tokens)
    last_index = tokens_count - 1

    for i, token in enumerate(tokens):
        assert token.index == i

        if i == 0:
            assert token.start_pos == 0
            assert token.end_pos == 0
            continue
        prev_token = tokens[i-1]
        assert prev_token.end_pos <= token.start_pos
        assert token.start_pos <= token.end_pos
        if i < last_index:
            next_token = tokens[i+1]
            assert token.end_pos <= next_token.start_pos

        if token.pair is not None:
            assert token.pair != token
            assert token.pair.pair is not None
            assert token.pair.pair == token

        assert token.chomp in ("+", "-", "")

    # jinja_token is None if lexer.wrap() skips it (eg whitespace)
    jinja_tokens = [t.jinja_token for t in tokens if t.jinja_token is not None]
    assert len(jinja_tokens) == jinja_token_count

    pairs = [t for t in tokens if t.pair is not None]
    assert len(pairs)/2 == token_pairs_count

    chomps = (t.chomp for t in tokens if t.chomp)
    assert chomps == exepected_chomps
