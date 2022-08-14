from typing import Optional

from dataclasses import dataclass
from jinja2.lexer import newline_re, Token as JinjaToken


@dataclass
class Token:
    """Wrapper around JinjaToken to add details like characters consumed."""

    index: int

    # pos slices a template (ie: include start, exclude end): [start_pos:end_pos]
    start_pos: int
    end_pos: int  # if including whitespace, should equal next Token's start_pos

    # data from Lexer.tokeniter
    lineno: int
    token: str
    value_str: str

    jinja_token: Optional[JinjaToken] = None
    # jinja_token can have type and str modified by Lexer.wrap()
    # .lineno: int
    # .type: str
    # .value: Any  # declared as str, but this can be int, float, str, etc

    # Many tokens come in a pair. This is the other token in this pair.
    # For example: matching brackets in an expression
    # or sthe start/close of vars, blocks, comments.
    pair: Optional["Token"] = None


def normalize_newlines(source: str) -> str:
    """normalize newlines in template source like lexer.tokeniter does."""
    lines = newline_re.split(source)[::2]

    if not lexer.keep_trailing_newline and lines[-1] == "":
        del lines[-1]

    return "\n".join(lines)


def something(
    source: str,
    name: Optional[str] = None,
    filename: Optional[str] = None,
    state: Optional[str] = None,
):
    normalized_source = normalize_newlines(source)
    paired_tokens: List[Token] = []
    previous_token: Optional[Token] = None

    for index, token_tuple in enumerate(lexer.tokeniter(source, name, filename, state)):
        lineno, token, value_str = token_tuple

        start_pos = normalized_source.index(value_str)
        end_pos = start_pos + len(value_str)
        if previous_token is not None and start_pos > previous_token.end_pos:
            # space was stripped/chomped
            pass

        jinja_token: Optional[JinjaToken] = None  # None if skipped by wrap()
        for jinja_token in lexer.wrap(iter([token_tuple])):
            # if we got here, then wrap did not skip the token
            pass

        token = previous_token = Token(
            index, start_pos, end_pos, lineno, token, value_str, jinja_token
        )

        is_pair_opener = is_pair_closer = False
        # see if this token should have a pair
        if token == TOKEN_OPERATOR:
            if value_str in ("{", "(", "["):
                is_pair_opener = True
            elif value_str in ("}", ")", "]"):
                is_pair_closer = True
        elif token in (
            TOKEN_BLOCK_BEGIN,
            TOKEN_VARIABLE_BEGIN,
            TOKEN_RAW_BEGIN,
            TOKEN_COMMENT_BEGIN,
            TOKEN_LINESTATEMENT_BEGIN,
            TOKEN_LINECOMMENT_BEGIN,
        ):
            is_pair_opener = True
        elif token in (
            TOKEN_BLOCK_END,
            TOKEN_VARIABLE_END,
            TOKEN_RAW_END,
            TOKEN_COMMENT_END,
            TOKEN_LINESTATEMENT_END,
            TOKEN_LINECOMMENT_END,
        ):
            is_pair_closer = True

        if is_pair_opener:
            paired_tokens.append(token)
        elif is_pair_closer:
            open_token = paired_tokens.pop()
            open_token.pair = token
            token.pair = open_token

        yield token
