"""Expanded Jinja tokens iterator that avoids whitespace/comment/chomp data loss."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Iterator, Literal, Sequence, overload

from jinja2.lexer import (
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
    TOKEN_WHITESPACE,
    Lexer,
)
from jinja2.lexer import Token as JinjaToken
from jinja2.lexer import newline_re

# BEGIN_TOKENS and END_TOKENS should be in the same order (for tests)
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

SPACE = " "


# pylint: disable=too-many-instance-attributes
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

    jinja_token: JinjaToken | None = None
    # jinja_token can have type and str modified by Lexer.wrap()
    # .lineno: int
    # .type: str
    # .value: Any  # declared as str, but this can be int, float, str, etc
    #   when str, this is normalized to use configured newline_sequence

    # Many tokens come in a pair. This is the other token in this pair.
    # For example: matching brackets in an expression
    # or the start/close of vars, blocks, comments.
    pair: Token | None = None

    # chomp indicator (only used for start/end pairs) aka strip_sign
    chomp: Literal["+", "-", ""] = ""


def pre_iter_normalize_newlines(source: str, keep_trailing_newline: bool) -> str:
    """Normalize newlines in template source like lexer.tokeniter does."""
    lines = newline_re.split(source)[::2]

    if not keep_trailing_newline and lines[-1] == "":
        del lines[-1]

    return "\n".join(lines)


# pylint: disable=too-many-locals,too-many-branches,too-many-arguments,too-many-statements
def tokeniter(  # noqa: C901  # splitting this up would hurt readability
    lexer: Lexer,
    source: str,
    name: str | None = None,
    filename: str | None = None,
    state: str | None = None,
) -> Iterator[Token]:
    """Iterate over the lexed tokens of the given source using our Token wrapper."""
    normalized_source = pre_iter_normalize_newlines(source, lexer.keep_trailing_newline)
    paired_tokens: list[Token] = []
    index = 0
    start_pos = end_pos = prev_token_end_pos = 0
    lineno = 1

    yield Token(
        index=index,
        start_pos=start_pos,
        end_pos=end_pos,
        lineno=lineno,
        token=TOKEN_INITIAL,
        value_str="",
        jinja_token=None,
    )

    for index, token_tuple in enumerate(
        lexer.tokeniter(source, name, filename, state), 1
    ):
        lineno, token_type, value_str = token_tuple

        start_pos = normalized_source.index(value_str, prev_token_end_pos)
        consumed = len(value_str)
        end_pos = start_pos + consumed

        jinja_token: JinjaToken | None
        try:
            jinja_token = next(lexer.wrap(iter([token_tuple])))
        except StopIteration:
            # wrap skipped the token
            jinja_token = None

        is_pair_opener = is_pair_closer = False
        chomp: Literal["+", "-", ""] = ""

        # see if this token should have a pair
        if token_type == TOKEN_OPERATOR:
            if value_str in ("{", "(", "["):
                is_pair_opener = True
            elif value_str in ("}", ")", "]"):
                is_pair_closer = True

        elif token_type in BEGIN_TOKENS:
            is_pair_opener = True
            if normalized_source[end_pos - 1] in ("+", "-"):
                # chomp = normalized_source[end_pos]
                chomp = value_str[-1]  # type: ignore # value_str = "{%-"
            elif token_type == TOKEN_RAW_BEGIN:
                # value_str = "{%- raw %}"
                if "+" in value_str:
                    chomp = "+"
                elif "-" in value_str:
                    chomp = "-"

        elif token_type in END_TOKENS:
            is_pair_closer = True
            if normalized_source[start_pos] in ("+", "-"):
                # chomp = normalized_source[start_pos]
                chomp = value_str[0]  # type: ignore # value_str = "-%}\n    "
            elif token_type == TOKEN_RAW_END:
                # value_str = "{% endraw -%}"
                if "+" in value_str:
                    chomp = "+"
                elif "-" in value_str:
                    chomp = "-"

        # Jinja2 includes post-chomped whitespace in value_str (eg "-}}\n\n")
        # but the regex does not capture pre-chomped whitespace (eg "\n\n{{-")
        # so, recapture chomped whitespace before pair openers.
        # NB: raw end token is effectively an opener as it includes {% and %}.
        if (
            (is_pair_opener or token_type == TOKEN_RAW_END)
            and chomp == "-"
            and prev_token_end_pos < start_pos
        ):
            whitespace = normalized_source[prev_token_end_pos:start_pos]
            value_str = whitespace + value_str
            start_pos = prev_token_end_pos

        token = Token(
            index=index,
            start_pos=start_pos,
            end_pos=end_pos,
            lineno=lineno,
            token=token_type,
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

        prev_token_end_pos = token.end_pos

    yield Token(
        index=index + 1,
        start_pos=end_pos,
        end_pos=len(source),
        lineno=lineno,
        token=TOKEN_EOF,
        value_str="",
        jinja_token=None,
    )


class AbstractTokensCollection(ABC):
    """An abstract collection of Tokens."""

    tokens: tuple[Token, ...] | list[Token]
    index: int

    @property
    def current(self) -> Token:
        """Get the current Token."""
        return self.tokens[self.index]

    def __index__(self) -> int:
        """Return the index of the current token."""
        return self.index

    def __bool__(self) -> bool:
        """Return True if there are still tokens left to consume."""
        return 0 <= self.index < len(self.tokens)

    def __len__(self) -> int:
        """Return the tokens count."""
        return len(self.tokens)

    @overload
    def __getitem__(self, index: slice) -> Sequence[Token]:
        """Return the tokens in the given slice."""

    @overload
    def __getitem__(self, index: int) -> Token:
        """Return the token at the given index."""

    def __getitem__(self, index: int | slice) -> Token | Sequence[Token]:
        """Return the token(s) at the given index or slice."""
        return self.tokens[index]


class Tokens(AbstractTokensCollection):
    """A collection of Tokens."""

    tokens: tuple[Token, ...]

    def __init__(
        self,
        lexer: Lexer,
        source: str,
        name: str | None = None,
        filename: str | None = None,
        state: str | None = None,
    ):
        """Initialize a Tokens instance by lexing the source."""
        # We need to go through all the tokens to populate the token pair details
        self.tokens = tuple(tokeniter(lexer, source, name, filename, state))
        self.index = -1
        self.source_position = 0

    def seek(
        self, token_type: str, value: str | None = None
    ) -> tuple[list[Token], Token | None]:
        """Seek for a token of the given type, and optionally the given value.

        This seeks from the current Token until the target token is consumed.
        So, the current token is the target token + 1.
        """
        skipped = []
        # start with the current token
        token = self.current
        while True:
            # pylint: disable=too-many-boolean-expressions
            if (
                token.token == token_type
                or (
                    token.jinja_token is not None
                    and token.jinja_token.type == token_type
                )
            ) and (
                value is None
                or value == token.value_str
                # for strings, value_str includes quotes but jinja_token.value does not
                or (token.jinja_token is not None and value == token.jinja_token.value)
            ):
                break
            if token.token != TOKEN_INITIAL:
                skipped.append(token)
            try:
                token = next(self)
            except StopIteration:
                return skipped, None
        # the next seek should start from the next token
        try:
            next(self)
        except StopIteration:
            pass
        return skipped, token

    def __iter__(self) -> Tokens:
        """Return this Tokens instance, which is an iterator."""
        return self

    def __next__(self) -> Token:
        """Return the next token, advancing both index and source_position.

        This consumes the current token. The returned token is the new current token.
        When this reaches the end, StopIteration is raised (as defined by the iterator
        protocol) and the tokens index gets reset to -1. So, the last token is still
        the "current" token, but the next iteration will start from the beginning.
        """
        self.index += 1
        try:
            token = self.current
        except IndexError as exc:
            # reset for the next iteration, but leave source_position alone
            # for subsequent inspection.
            self.index = -1
            raise StopIteration from exc
        self.source_position = token.end_pos
        return token

    @property
    def end(self) -> bool:
        """Return True if there are no more tokens left."""
        return not self

    def __contains__(self, item: Token) -> bool:
        """Return True if the given token is the same as the token at the same index."""
        if not isinstance(item, Token):
            return False
        return 0 <= item.index < len(self) and item == self[item.index]


class TokenStream(AbstractTokensCollection):
    """A writable stream of Tokens that facilitates backtracking."""

    tokens: list[Token]

    def __init__(
        self,
        max_line_length: int,
        max_first_line_length: int | None = None,
    ) -> None:
        """Initialize a TokenStream instance."""
        if max_first_line_length is None:
            max_first_line_length = max_line_length
        self.max_line_length = max_line_length
        self.max_first_line_length = max_first_line_length
        self.line_position = 0
        self.line_number = 1

        self.index = -1
        self.tokens = []
        self.append(TOKEN_INITIAL, "")

    @property
    def _max_line_position(self) -> int:
        if self.line_number == 1:
            return self.max_first_line_length
        return self.max_line_length

    def append(self, token: str, value: str, chomp: Literal["+", "-", ""] = "") -> None:
        """Add a Jinja token type with the given value."""
        index = len(self.tokens)
        if token == TOKEN_WHITESPACE and value is SPACE:
            previous = self.tokens[index - 1]
            if previous.token == TOKEN_WHITESPACE:
                # no more than one consecutive space
                return

        len_value = len(value)
        newline_pos = value.rfind("\n")
        line_pos = self.line_position
        if newline_pos == -1:
            line_pos += len_value
        else:
            # - 1 to exclude the \n
            line_pos = len_value - newline_pos - 1
        if value is SPACE and (line_pos >= self._max_line_position):
            value = "\n"
            line_pos = 0

        self.tokens.append(
            Token(
                index=index,
                start_pos=-1,
                end_pos=-1,
                lineno=-1,
                token=token,
                value_str=value,
                jinja_token=None,
                chomp=chomp,
            )
        )
        self.index = index
        self.line_position = line_pos
        self.line_number += value.count("\n")

    def extend(self, *args: tuple[str, str]) -> None:
        """Extend with the given set of Jinja token type and value tuples."""
        for token, value in args:
            self.append(token, value)

    def insert(
        self, index: int, token: str, value: str, chomp: Literal["+", "-", ""] = ""
    ) -> None:
        """Insert a Jinja token type with the given value at the given index."""
        # this does not prevent duplicate whitespace
        self.tokens.insert(
            index,
            Token(
                index=index,
                start_pos=-1,
                end_pos=-1,
                lineno=-1,
                token=token,
                value_str=value,
                jinja_token=None,
                chomp=chomp,
            ),
        )
        for _index, _token in enumerate(self.tokens[index:], start=index):
            _token.index = _index
        self.index = len(self.tokens)

    def clear(self) -> None:
        """Reset the tokens."""
        self.tokens.clear()
        self.line_position = 0
        self.line_number = 1
        self.index = -1
        self.append(TOKEN_INITIAL, "")

    def close(self) -> None:
        """Add the EOF token."""
        self.append(TOKEN_EOF, "")

    def reindex(self) -> None:
        """Update the indexes for all tokens."""
        for index, token in enumerate(self.tokens):
            token.index = index

    def __str__(self) -> str:
        """Stringify the list of tokens."""
        return "".join(token.value_str for token in self.tokens)
