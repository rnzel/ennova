# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Object-oriented polymorphic writing modes
from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.domain.diary import StoredEntry
from app.domain.processing import CorrectionRule, correct, diff, normalize

from .models import DerivedVersion, ReviewSuggestion

LONG_SENTENCE_WORD_THRESHOLD = 25
_WORD_PATTERN = re.compile(r"[^\W_]+(?:['-][^\W_]+)*", re.UNICODE)
_SENTENCE_PATTERN = re.compile(r"[^.!?]+(?:[.!?]+|$)", re.DOTALL)
_LONG_MESSAGE = "Sentence exceeds the long-sentence word threshold."
_REPEATED_MESSAGE = "Adjacent words are repeated."
_PUNCTUATION_MESSAGE = "Entry is missing terminal punctuation."


class WritingMode(ABC):
    """Abstract strategy for deriving a version without changing its source."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable policy name for this mode."""

    @abstractmethod
    def process(self, entry: StoredEntry) -> DerivedVersion:
        """Derive one immutable version from a stored original entry."""

    @staticmethod
    def _require_entry(entry: StoredEntry) -> StoredEntry:
        if not isinstance(entry, StoredEntry):
            raise TypeError("entry must be a StoredEntry.")
        return entry


class Verbatim(WritingMode):
    """Preserve the original text exactly."""

    @property
    def name(self) -> str:
        return "verbatim"

    def process(self, entry: StoredEntry) -> DerivedVersion:
        source = self._require_entry(entry)
        return DerivedVersion(
            source.entry.entry_id,
            source.chain_entry.digest,
            self.name,
            source.entry.original_content,
            (),
        )


class LightFix(WritingMode):
    """Apply only caller-supplied pure normalization and corrections."""

    def __init__(self, correction_rules: tuple[CorrectionRule, ...] = ()) -> None:
        if not isinstance(correction_rules, tuple) or any(
            not isinstance(rule, CorrectionRule) for rule in correction_rules
        ):
            raise TypeError("correction_rules must be a tuple of CorrectionRule values.")
        self._correction_rules = correction_rules

    @property
    def name(self) -> str:
        return "light_fix"

    def process(self, entry: StoredEntry) -> DerivedVersion:
        source = self._require_entry(entry)
        original = source.entry.original_content
        updated = correct(normalize(original), self._correction_rules)
        return DerivedVersion(
            source.entry.entry_id,
            source.chain_entry.digest,
            self.name,
            updated,
            diff(original, updated),
        )


class Review(WritingMode):
    """Report deterministic findings and optionally apply rule-based corrections."""

    def __init__(
        self,
        correction_rules: tuple[CorrectionRule, ...] = (),
        *,
        rewrite: bool = False,
    ) -> None:
        if not isinstance(correction_rules, tuple) or any(
            not isinstance(rule, CorrectionRule) for rule in correction_rules
        ):
            raise TypeError("correction_rules must be a tuple of CorrectionRule values.")
        if not isinstance(rewrite, bool):
            raise TypeError("rewrite must be a bool.")
        self._correction_rules = correction_rules
        self._rewrite = rewrite

    @property
    def name(self) -> str:
        return "review"

    def process(self, entry: StoredEntry) -> DerivedVersion:
        source = self._require_entry(entry)
        original = source.entry.original_content
        updated = (
            correct(normalize(original), self._correction_rules)
            if self._rewrite
            else original
        )
        return DerivedVersion(
            source.entry.entry_id,
            source.chain_entry.digest,
            self.name,
            updated,
            diff(original, updated),
            _review_suggestions(original),
        )


def _review_suggestions(text: str) -> tuple[ReviewSuggestion, ...]:
    suggestions: list[ReviewSuggestion] = []
    for sentence in _SENTENCE_PATTERN.finditer(text):
        words = tuple(_WORD_PATTERN.finditer(sentence.group()))
        if len(words) > LONG_SENTENCE_WORD_THRESHOLD:
            suggestions.append(
                ReviewSuggestion(
                    "long_sentence", sentence.start(), _LONG_MESSAGE
                )
            )
    words = tuple(_WORD_PATTERN.finditer(text))
    for previous, current in zip(words, words[1:]):
        if previous.group().casefold() == current.group().casefold():
            suggestions.append(
                ReviewSuggestion(
                    "repeated_word", current.start(), _REPEATED_MESSAGE
                )
            )
    if text.strip() and text.rstrip()[-1] not in ".!?":
        suggestions.append(
            ReviewSuggestion(
                "missing_terminal_punctuation",
                len(text.rstrip()),
                _PUNCTUATION_MESSAGE,
            )
        )
    return tuple(suggestions)
