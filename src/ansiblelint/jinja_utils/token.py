from typing import Iterator, List, Literal, Optional

from dataclasses import dataclass
from jinja2.lexer import (
    Lexer,
    TOKEN_BLOCK_BEGIN,
    TOKEN_BLOCK_END,
    TOKEN_COMMENT_BEGIN,
    TOKEN_COMMENT_END,
    TOKEN_EOF,
    TOKEN_INITIAL,
    TOKEN_LINECOMMENT_BEGIN,
    TOKEN_LINECOMMENT_END,
    TOKEN_LINESTATEMENT_BEGIN,
    TOKEN_LINESTATEMENT_END,
    TOKEN_OPERATOR,
    TOKEN_RAW_BEGIN,
    TOKEN_RAW_END,
    TOKEN_VARIABLE_BEGIN,
    TOKEN_VARIABLE_END,
    Token as JinjaToken,
    newline_re,
)


BEGIN_TOKENS = (
    TOKEN_BLOCK_BEGIN,
    TOKEN_VARIABLE_BEGIN,
    TOKEN_RAW_BEGIN,
    TOKEN_COMMENT_BEGIN,
    TOKEN_LINESTATEMENT_BEGIN,
    TOKEN_LINECOMMENT_BEGIN,
)
END_TOKENS = (
    TOKEN_BLOCK_END,
    TOKEN_VARIABLE_END,
    TOKEN_RAW_END,
    TOKEN_COMMENT_END,
    TOKEN_LINESTATEMENT_END,
    TOKEN_LINECOMMENT_END,
)


@dataclass  # this is mutable and DOES change after creation
class Token:
    """Wrapper around JinjaToken to add details like characters consumed."""

    index: int

    # pos slices a template (ie: include start, exclude end): [start_pos:end_pos]
    # NB: this is the pos with new lines normalized to \n
    start_pos: int
    end_pos: int

    # data from Lexer.tokeniter
    lineno: int
    token: str
    value_str: str

    jinja_token: Optional[JinjaToken] = None
    # jinja_token can have type and str modified by Lexer.wrap()
    # .lineno: int
    # .type: str
    # .value: Any  # declared as str, but this can be int, float, str, etc
    #   when str, this is normalized to use configured newline_sequence

    # Many tokens come in a pair. This is the other token in this pair.
    # For example: matching brackets in an expression
    # or sthe start/close of vars, blocks, comments.
    pair: Optional["Token"] = None

    # chomp indicator (only used for start/end pairs) aka strip_sign
    chomp: Literal["+", "-", ""] = ""


def pre_iter_normalize_newlines(source: str, keep_trailing_newline: bool) -> str:
    """normalize newlines in template source like lexer.tokeniter does."""
    lines = newline_re.split(source)[::2]

    if not keep_trailing_newline and lines[-1] == "":
        del lines[-1]

    return "\n".join(lines)


def tokeniter(
    lexer: Lexer,
    source: str,
    name: Optional[str] = None,
    filename: Optional[str] = None,
    state: Optional[str] = None,
) -> Iterator[Token]:
    normalized_source = pre_iter_normalize_newlines(source, lexer.keep_trailing_newline)
    paired_tokens: List[Token] = []
    index = 0
    start_pos = end_pos = 0
    lineno = 1

    yield Token(
        index=index,
        start_pos=start_pos,
        end_pos=end_pos,
        lineno=lineno,
        token=TOKEN_INITIAL,
        value_str="",
        jinja_token=JinjaToken(1, TOKEN_INITIAL, ""),
    )

    for index, token_tuple in enumerate(
        lexer.tokeniter(source, name, filename, state), 1
    ):
        lineno, raw_token, value_str = token_tuple

        start_pos = normalized_source.index(value_str, end_pos)
        consumed = len(value_str)
        end_pos = start_pos + consumed

        jinja_token: Optional[JinjaToken]
        try:
            jinja_token = next(lexer.wrap(iter([token_tuple])))
        except StopIteration:
            # wrap skipped the token
            jinja_token = None

        is_pair_opener = is_pair_closer = False
        chomp: Literal["+", "-", ""] = ""

        # see if this token should have a pair
        if raw_token == TOKEN_OPERATOR:
            if value_str in ("{", "(", "["):
                is_pair_opener = True
            elif value_str in ("}", ")", "]"):
                is_pair_closer = True

        elif raw_token in BEGIN_TOKENS:
            is_pair_opener = True
            if normalized_source[end_pos - 1] in ("+", "-"):
                # chomp = normalized_source[end_pos]
                chomp = value_str[-1]  # value_str = "{%-"

        elif raw_token in END_TOKENS:
            is_pair_closer = True
            if normalized_source[start_pos] in ("+", "-"):
                # chomp = normalized_source[start_pos]
                chomp = value_str[0]  # value_str = "-%}\n    "

        token = Token(
            index=index,
            start_pos=start_pos,
            end_pos=end_pos,
            lineno=lineno,
            token=raw_token,
            value_str=value_str,
            jinja_token=jinja_token,
            # pair gets added later if needed
            chomp=chomp,
        )

        # we assume the template is valid and was previously fully parsed
        if is_pair_opener:
            paired_tokens.append(token)
        elif is_pair_closer:
            open_token = paired_tokens.pop()
            open_token.pair = token
            token.pair = open_token

        yield token

    yield Token(
        index=index + 1,
        start_pos=end_pos,
        end_pos=len(normalized_source),
        lineno=lineno,
        token=TOKEN_EOF,
        value_str="",
        jinja_token=JinjaToken(lineno, TOKEN_EOF, ""),
    )
