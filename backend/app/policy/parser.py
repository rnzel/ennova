# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Language design / recursive-descent parsing
from __future__ import annotations

from datetime import date

from app.errors import PolicySyntaxError

from .ast_nodes import (
    DefaultWritingMode,
    MayNotRead,
    MayNotSeeExistence,
    MayRead,
    MaySeeExistence,
    MentioningSelector,
    Policy,
    ProtocolBlock,
    ProtocolStatement,
    ReleaseLetter,
    Selector,
    TaggedSelector,
    TopLevelStatement,
    TransferCustody,
    Trustee,
)
from .lexer import Token, TokenKind, lex


class Parser:
    """Recursive-descent parser with a dedicated method for every grammar rule."""

    def __init__(self, tokens: tuple[Token, ...]) -> None:
        """Create a parser over an immutable token sequence."""
        self._tokens = tokens
        self._position = 0

    @property
    def _current(self) -> Token:
        """Return the token currently under consideration."""
        return self._tokens[self._position]

    def _advance(self) -> Token:
        """Consume and return the current token."""
        token = self._current
        if token.kind is not TokenKind.EOF:
            self._position += 1
        return token

    def _match_keyword(self, keyword: str) -> bool:
        """Consume a matching keyword and report whether it was present."""
        if self._current.kind is TokenKind.KEYWORD and self._current.value == keyword:
            self._advance()
            return True
        return False

    def _expect(self, kind: TokenKind, description: str) -> Token:
        """Consume a token of the requested kind or raise at its source location."""
        token = self._current
        if token.kind is not kind:
            if token.kind is TokenKind.INVALID_IDENTIFIER:
                raise PolicySyntaxError(
                    "identifiers are lowercase and must match [a-z][a-z0-9_]*.",
                    token.line,
                    token.column,
                )
            if token.kind is TokenKind.KEYWORD and kind is TokenKind.IDENT:
                message = f"Expected {description}; reserved words cannot be identifiers."
            else:
                message = f"Expected {description}."
            raise PolicySyntaxError(message, token.line, token.column)
        return self._advance()

    def _expect_keyword(self, keyword: str) -> Token:
        """Consume a keyword or raise a location-aware syntax error."""
        token = self._current
        if token.kind is not TokenKind.KEYWORD or token.value != keyword:
            raise PolicySyntaxError(
                f"Expected '{keyword}'.", token.line, token.column
            )
        return self._advance()

    def _expect_newline(self) -> None:
        """Consume the newline terminating a source line."""
        self._expect(TokenKind.NEWLINE, "a newline")

    def parse_program(self) -> Policy:
        """Parse the program nonterminal into an immutable policy AST."""
        statements: list[TopLevelStatement] = []
        while self._current.kind is not TokenKind.EOF:
            if self._current.kind is TokenKind.NEWLINE:
                self._advance()
                continue
            if self._current.kind in (TokenKind.INDENT, TokenKind.DEDENT):
                token = self._current
                raise PolicySyntaxError(
                    "Unexpected indentation outside a protocol block.",
                    token.line,
                    token.column,
                )
            statement = self.parse_top_level_line()
            statements.append(statement)
            if isinstance(statement, ProtocolBlock):
                continue
            if self._current.kind is TokenKind.NEWLINE:
                self._advance()
            elif self._current.kind is not TokenKind.EOF:
                token = self._current
                raise PolicySyntaxError(
                    "Expected the end of the source line.",
                    token.line,
                    token.column,
                )
        return Policy(tuple(statements))

    def parse_top_level_line(self) -> TopLevelStatement:
        """Parse one top-level statement or protocol block."""
        token = self._current
        if token.kind is TokenKind.KEYWORD and token.value == "protocol":
            return self.parse_protocol_block()
        if token.kind is TokenKind.KEYWORD and token.value == "trustee":
            return self.parse_trustee_statement()
        return self.parse_global_statement()

    def parse_protocol_block(self) -> ProtocolBlock:
        """Parse a protocol block, including an allowed empty body."""
        self._expect_keyword("protocol")
        person = self.parse_identifier("protocol identifier")
        if self._current.kind is not TokenKind.COLON:
            token = self._current
            raise PolicySyntaxError(
                "Expected ':' after protocol identifier.", token.line, token.column
            )
        self._advance()
        self._expect_newline()

        statements: list[ProtocolStatement] = []
        if self._current.kind is TokenKind.INDENT:
            self._advance()
            while self._current.kind is not TokenKind.DEDENT:
                if self._current.kind is TokenKind.EOF:
                    token = self._current
                    raise PolicySyntaxError(
                        "Expected the end of the protocol block.",
                        token.line,
                        token.column,
                    )
                statements.append(self.parse_protocol_line())
                self._expect_newline()
            self._advance()
        return ProtocolBlock(person, tuple(statements))

    def parse_protocol_line(self) -> ProtocolStatement:
        """Parse one grant or deny statement inside a protocol block."""
        self._expect_keyword("may")
        if self._match_keyword("not"):
            return self.parse_deny_statement()
        return self.parse_grant_statement()

    def parse_grant_statement(self) -> ProtocolStatement:
        """Parse one positive access grant."""
        if self._match_keyword("see"):
            return self.parse_may_see_statement()
        if self._match_keyword("read"):
            return self.parse_may_read_statement()
        token = self._current
        raise PolicySyntaxError("Expected 'see' or 'read'.", token.line, token.column)

    def parse_deny_statement(self) -> ProtocolStatement:
        """Parse one explicit access denial."""
        if self._match_keyword("see"):
            return self.parse_may_not_see_statement()
        if self._match_keyword("read"):
            return self.parse_may_not_read_statement()
        token = self._current
        raise PolicySyntaxError("Expected 'see' or 'read'.", token.line, token.column)

    def parse_may_see_statement(self) -> MaySeeExistence:
        """Parse 'may see existence of selector'."""
        self._expect_keyword("existence")
        self._expect_keyword("of")
        return MaySeeExistence(self.parse_selector())

    def parse_may_read_statement(self) -> MayRead:
        """Parse 'may read summary|verbatim of selector'."""
        level = self.parse_access_level()
        self._expect_keyword("of")
        return MayRead(level, self.parse_selector())

    def parse_may_not_see_statement(self) -> MayNotSeeExistence:
        """Parse 'may not see existence of selector'."""
        self._expect_keyword("existence")
        self._expect_keyword("of")
        return MayNotSeeExistence(self.parse_selector())

    def parse_may_not_read_statement(self) -> MayNotRead:
        """Parse 'may not read summary|verbatim of selector'."""
        level = self.parse_access_level()
        self._expect_keyword("of")
        return MayNotRead(level, self.parse_selector())

    def parse_access_level(self) -> str:
        """Parse the summary or verbatim access-level nonterminal."""
        token = self._current
        if token.kind is TokenKind.KEYWORD and token.value in ("summary", "verbatim"):
            self._advance()
            return token.value
        raise PolicySyntaxError(
            "Expected access level 'summary' or 'verbatim'.",
            token.line,
            token.column,
        )

    def parse_selector(self) -> Selector:
        """Parse one selector alternative."""
        self._expect_keyword("entries")
        if self._match_keyword("mentioning"):
            return self.parse_mentioning_selector()
        if self._match_keyword("tagged"):
            return self.parse_tagged_selector()
        token = self._current
        raise PolicySyntaxError(
            "Expected 'mentioning' or 'tagged'.", token.line, token.column
        )

    def parse_mentioning_selector(self) -> MentioningSelector:
        """Parse a selector that names a person identifier."""
        return MentioningSelector(self.parse_identifier("person identifier"))

    def parse_tagged_selector(self) -> TaggedSelector:
        """Parse a selector with a quoted tag string."""
        token = self._expect(TokenKind.STRING, "a quoted tag")
        return TaggedSelector(token.value)

    def parse_global_statement(self) -> TopLevelStatement:
        """Parse a top-level release, custody, or default-mode statement."""
        token = self._current
        if token.kind is TokenKind.KEYWORD and token.value == "release":
            return self.parse_release_statement()
        if token.kind is TokenKind.KEYWORD and token.value == "transfer":
            return self.parse_custody_statement()
        if token.kind is TokenKind.KEYWORD and token.value == "default":
            return self.parse_default_mode_statement()
        raise PolicySyntaxError(
            "Expected a protocol, trustee, release, custody, or default-mode statement.",
            token.line,
            token.column,
        )

    def parse_release_statement(self) -> ReleaseLetter:
        """Parse a release-letter statement and validate its calendar date."""
        self._expect_keyword("release")
        self._expect_keyword("letter")
        title = self._expect(TokenKind.STRING, "a quoted letter title").value
        self._expect_keyword("to")
        person = self.parse_identifier("person identifier")
        self._expect_keyword("when")
        self._expect_keyword("date")
        self._expect(TokenKind.GE, "'>='")
        token = self._expect(TokenKind.DATE, "a YYYY-MM-DD date")
        try:
            release_date = date.fromisoformat(token.value)
        except ValueError as error:
            raise PolicySyntaxError(
                "Release date must be a valid calendar date in YYYY-MM-DD form.",
                token.line,
                token.column,
            ) from error
        return ReleaseLetter(title, person, release_date)

    def parse_custody_statement(self) -> TransferCustody:
        """Parse a custody-transfer rule without requiring a trustee statement."""
        self._expect_keyword("transfer")
        self._expect_keyword("custody")
        self._expect_keyword("to")
        person = self.parse_identifier("person identifier")
        self._expect_keyword("if")
        self._expect_keyword("trustee")
        self._expect_keyword("unavailable")
        self._expect_keyword("for")
        days = int(self._expect(TokenKind.INTEGER, "a day count").value)
        self._expect_keyword("days")
        return TransferCustody(person, days)

    def parse_trustee_statement(self) -> Trustee:
        """Parse the optional top-level trustee identity statement."""
        self._expect_keyword("trustee")
        self._expect_keyword("is")
        return Trustee(self.parse_identifier("person identifier"))

    def parse_default_mode_statement(self) -> DefaultWritingMode:
        """Parse the default writing mode statement."""
        self._expect_keyword("default")
        self._expect_keyword("writing")
        self._expect_keyword("mode")
        self._expect(TokenKind.COLON, "':'")
        return DefaultWritingMode(self.parse_writing_mode())

    def parse_writing_mode(self) -> str:
        """Parse the verbatim, light_fix, or review writing-mode nonterminal."""
        token = self._current
        if token.kind is TokenKind.KEYWORD and token.value in (
            "verbatim",
            "light_fix",
            "review",
        ):
            self._advance()
            return token.value
        raise PolicySyntaxError(
            "Expected writing mode 'verbatim', 'light_fix', or 'review'.",
            token.line,
            token.column,
        )

    def parse_identifier(self, description: str) -> str:
        """Parse one lowercase identifier token."""
        token = self._expect(TokenKind.IDENT, description)
        return token.value


def parse(source: str) -> Policy:
    """Lex and parse policy source into an immutable AST."""
    return Parser(lex(source)).parse_program()
