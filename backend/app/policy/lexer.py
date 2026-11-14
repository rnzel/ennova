# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Language design / lexical analysis
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum

from app.errors import PolicySyntaxError


class TokenKind(str, Enum):
    """Kinds of lexical units recognized by the policy lexer."""

    KEYWORD = "keyword"
    IDENT = "identifier"
    INVALID_IDENTIFIER = "invalid_identifier"
    STRING = "string"
    DATE = "date"
    INTEGER = "integer"
    COLON = "colon"
    GE = "greater_or_equal"
    NEWLINE = "newline"
    INDENT = "indent"
    DEDENT = "dedent"
    EOF = "eof"


@dataclass(frozen=True, slots=True)
class Token:
    """One immutable lexical token and its one-based source location."""

    kind: TokenKind
    value: str
    line: int
    column: int


_KEYWORDS = frozenset(
    {
        "protocol",
        "may",
        "see",
        "existence",
        "of",
        "read",
        "summary",
        "verbatim",
        "not",
        "entries",
        "mentioning",
        "tagged",
        "release",
        "letter",
        "to",
        "when",
        "date",
        "transfer",
        "custody",
        "if",
        "trustee",
        "unavailable",
        "for",
        "days",
        "is",
        "default",
        "writing",
        "mode",
        "light_fix",
        "review",
    }
)
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_LOWER_IDENTIFIER_RE = re.compile(r"[a-z][a-z0-9_]*")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_INTEGER_RE = re.compile(r"\d+")
_INDENT_WIDTH = 4


def _error(message: str, line: int, column: int) -> PolicySyntaxError:
    """Construct a location-aware syntax error."""
    return PolicySyntaxError(message, line, column)


def _scan_line(
    source_line: str, line_number: int, column_offset: int
) -> list[Token]:
    """Tokenize one nonblank line without its indentation or line ending."""
    tokens: list[Token] = []
    index = 0
    while index < len(source_line):
        char = source_line[index]
        if char in " \r":
            index += 1
            continue
        if char == "\t":
            raise _error("Tabs are not allowed; use spaces.", line_number, index + 1)

        column = index + column_offset + 1
        if char == '"':
            end = index + 1
            while end < len(source_line):
                if source_line[end] == "\\":
                    end += 2
                    continue
                if source_line[end] == '"':
                    break
                end += 1
            if end >= len(source_line):
                raise _error("Unterminated quoted string.", line_number, column)
            raw_string = source_line[index : end + 1]
            try:
                value = json.loads(raw_string)
            except json.JSONDecodeError as error:
                raise _error(
                    "Invalid quoted-string escape.",
                    line_number,
                    column + error.colno - 1,
                ) from error
            tokens.append(Token(TokenKind.STRING, value, line_number, column))
            index = end + 1
            continue

        if source_line.startswith(">=", index):
            tokens.append(Token(TokenKind.GE, ">=", line_number, column))
            index += 2
            continue
        if char == ":":
            tokens.append(Token(TokenKind.COLON, char, line_number, column))
            index += 1
            continue

        date_match = _DATE_RE.match(source_line, index)
        if date_match:
            tokens.append(Token(TokenKind.DATE, date_match.group(), line_number, column))
            index = date_match.end()
            continue

        integer_match = _INTEGER_RE.match(source_line, index)
        if integer_match:
            tokens.append(
                Token(TokenKind.INTEGER, integer_match.group(), line_number, column)
            )
            index = integer_match.end()
            continue

        identifier_match = _IDENTIFIER_RE.match(source_line, index)
        if identifier_match:
            value = identifier_match.group()
            if value in _KEYWORDS:
                kind = TokenKind.KEYWORD
            elif _LOWER_IDENTIFIER_RE.fullmatch(value):
                kind = TokenKind.IDENT
            else:
                kind = TokenKind.INVALID_IDENTIFIER
            tokens.append(Token(kind, value, line_number, column))
            index = identifier_match.end()
            continue

        raise _error(f"Unexpected character {char!r}.", line_number, column)
    return tokens


def lex(source: str) -> tuple[Token, ...]:
    """Tokenize policy source, enforcing one four-space indentation level."""
    if not isinstance(source, str):
        raise TypeError("source must be a string.")

    tokens: list[Token] = []
    indent_level = 0
    lines = source.splitlines()
    for line_number, source_line in enumerate(lines, start=1):
        if not source_line.strip():
            continue

        leading_spaces = len(source_line) - len(source_line.lstrip(" "))
        if source_line[:leading_spaces].find("\t") != -1:
            raise _error(
                "Tabs are not allowed; use four spaces for protocol indentation.",
                line_number,
                1,
            )
        if leading_spaces not in (0, _INDENT_WIDTH):
            raise _error(
                "Only one indentation level of four spaces is allowed.",
                line_number,
                1,
            )

        if leading_spaces != indent_level:
            token_kind = TokenKind.INDENT if leading_spaces else TokenKind.DEDENT
            tokens.append(Token(token_kind, "", line_number, 1))
            indent_level = leading_spaces

        tokens.extend(_scan_line(source_line[leading_spaces:], line_number, leading_spaces))
        tokens.append(Token(TokenKind.NEWLINE, "", line_number, len(source_line) + 1))

    if indent_level:
        tokens.append(Token(TokenKind.DEDENT, "", len(lines) + 1, 1))
    tokens.append(Token(TokenKind.EOF, "", len(lines) + 1, 1))
    return tuple(tokens)
