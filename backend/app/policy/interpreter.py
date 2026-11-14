# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Language design / AST interpretation
from __future__ import annotations

import re
import unicodedata

from .ast_nodes import (
    DefaultWritingMode,
    MayNotRead,
    MayNotSeeExistence,
    MayRead,
    MaySeeExistence,
    MentioningSelector,
    Policy,
    ProtocolBlock,
    ReleaseLetter,
    TaggedSelector,
    TransferCustody,
    Trustee,
)

_PLAIN_ATOM_RE = re.compile(r"[a-z][a-z0-9_]*")


def quote_prolog_atom(value: str) -> str:
    """Encode arbitrary text as a safe single-quoted Prolog atom."""
    if not isinstance(value, str):
        raise TypeError("Prolog atom values must be strings.")
    escaped: list[str] = []
    for char in value:
        codepoint = ord(char)
        if char == "\\":
            escaped.append("\\\\")
        elif char == "'":
            escaped.append("\\'")
        elif char == "\n":
            escaped.append("\\n")
        elif char == "\r":
            escaped.append("\\r")
        elif char == "\t":
            escaped.append("\\t")
        elif char == "\b":
            escaped.append("\\b")
        elif char == "\f":
            escaped.append("\\f")
        elif unicodedata.category(char) == "Cc":
            escaped.append(f"\\x{codepoint:x}\\")
        else:
            escaped.append(char)
    return "'" + "".join(escaped) + "'"


def _quote_atom(value: str) -> str:
    """Keep the original private helper name for existing interpreter calls."""
    return quote_prolog_atom(value)


def _atom(value: str) -> str:
    """Serialize a lowercase plain atom or safely quote arbitrary text."""
    normalized = value.casefold()
    if _PLAIN_ATOM_RE.fullmatch(normalized):
        return normalized
    return quote_prolog_atom(normalized)


def _selector_term(selector: MentioningSelector | TaggedSelector) -> str:
    """Serialize a selector as the specified Prolog term."""
    if isinstance(selector, MentioningSelector):
        return f"mentioning({_atom(selector.name)})"
    if isinstance(selector, TaggedSelector):
        return f"tagged({_atom(selector.tag)})"
    raise TypeError("Unsupported selector AST node.")


def _protocol_facts(block: ProtocolBlock) -> tuple[str, ...]:
    """Interpret one protocol block without merging repeated blocks."""
    facts: list[str] = []
    for statement in block.statements:
        if isinstance(statement, MaySeeExistence):
            facts.append(
                f"grant({_atom(block.person)}, existence, "
                f"{_selector_term(statement.selector)})."
            )
        elif isinstance(statement, MayRead):
            if statement.level not in ("summary", "verbatim"):
                raise ValueError(f"Unsupported grant level: {statement.level}")
            facts.append(
                f"grant({_atom(block.person)}, {_atom(statement.level)}, "
                f"{_selector_term(statement.selector)})."
            )
        elif isinstance(statement, MayNotSeeExistence):
            facts.append(
                f"deny({_atom(block.person)}, existence, "
                f"{_selector_term(statement.selector)})."
            )
        elif isinstance(statement, MayNotRead):
            if statement.level not in ("summary", "verbatim"):
                raise ValueError(f"Unsupported deny level: {statement.level}")
            facts.append(
                f"deny({_atom(block.person)}, {_atom(statement.level)}, "
                f"{_selector_term(statement.selector)})."
            )
        else:
            raise TypeError(f"Unsupported protocol AST node: {type(statement).__name__}")
    return tuple(facts)


def interpret(policy: Policy) -> tuple[str, ...]:
    """Translate each written policy statement into one Prolog fact in source order."""
    if not isinstance(policy, Policy):
        raise TypeError("policy must be a Policy AST.")

    facts: list[str] = []
    for statement in policy.statements:
        if isinstance(statement, ProtocolBlock):
            facts.extend(_protocol_facts(statement))
        elif isinstance(statement, ReleaseLetter):
            release_date = statement.release_date
            facts.append(
                f"release({_atom(statement.person)}, {quote_prolog_atom(statement.title)}, "
                f"date({release_date.year},{release_date.month},{release_date.day}))."
            )
        elif isinstance(statement, Trustee):
            facts.append(f"trustee({_atom(statement.person)}).")
        elif isinstance(statement, TransferCustody):
            facts.append(
                "custody_rule("
                f"{_atom(statement.person)}, trustee_unavailable, "
                f"{statement.unavailable_days})."
            )
        elif isinstance(statement, DefaultWritingMode):
            if statement.mode not in ("verbatim", "light_fix", "review"):
                raise ValueError(f"Unsupported writing mode: {statement.mode}")
            facts.append(f"default_mode({_atom(statement.mode)}).")
        else:
            raise TypeError(f"Unsupported top-level AST node: {type(statement).__name__}")
    return tuple(facts)
