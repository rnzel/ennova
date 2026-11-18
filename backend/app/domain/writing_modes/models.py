# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Object-oriented immutable writing-mode results
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.domain.processing import DiffSegment

SuggestionCode = Literal[
    "long_sentence",
    "repeated_word",
    "missing_terminal_punctuation",
]
_MESSAGES = {
    "long_sentence": "Sentence exceeds the long-sentence word threshold.",
    "repeated_word": "Adjacent words are repeated.",
    "missing_terminal_punctuation": "Entry is missing terminal punctuation.",
}


@dataclass(frozen=True, slots=True)
class ReviewSuggestion:
    """One deterministic review finding at a character position."""

    code: SuggestionCode
    position: int
    message: str

    def __post_init__(self) -> None:
        """Validate the immutable suggestion record."""
        if self.code not in (
            "long_sentence",
            "repeated_word",
            "missing_terminal_punctuation",
        ):
            raise ValueError("code is not a supported review suggestion.")
        if not isinstance(self.position, int) or self.position < 0:
            raise ValueError("position must be a non-negative integer.")
        if self.message != _MESSAGES[self.code]:
            raise ValueError("message does not match the suggestion code.")


@dataclass(frozen=True, slots=True)
class DerivedVersion:
    """Immutable text derived from one hash-chained original entry."""

    source_entry_id: str
    source_digest: str
    mode_name: str
    text: str
    changes: tuple[DiffSegment, ...]
    suggestions: tuple[ReviewSuggestion, ...] = ()

    def __post_init__(self) -> None:
        """Validate immutable source identity and result collections."""
        for value, field_name in (
            (self.source_entry_id, "source_entry_id"),
            (self.source_digest, "source_digest"),
            (self.mode_name, "mode_name"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string.")
        if not isinstance(self.text, str):
            raise TypeError("text must be a string.")
        if not isinstance(self.changes, tuple):
            raise TypeError("changes must be a tuple.")
        if any(not isinstance(item, DiffSegment) for item in self.changes):
            raise TypeError("changes must be DiffSegment values.")
        if not isinstance(self.suggestions, tuple) or any(
            not isinstance(item, ReviewSuggestion) for item in self.suggestions
        ):
            raise TypeError("suggestions must be ReviewSuggestion values.")
