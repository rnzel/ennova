# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Functional entry processing data
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class PersonReference:
    """Immutable known-person data used for deterministic name extraction."""

    person_id: str
    canonical_name: str
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate identity strings and the immutable alias collection."""
        if not isinstance(self.person_id, str) or not self.person_id.strip():
            raise ValueError("person_id must be a non-empty string.")
        if not isinstance(self.canonical_name, str) or not self.canonical_name.strip():
            raise ValueError("canonical_name must be a non-empty string.")
        if not isinstance(self.aliases, tuple):
            raise TypeError("aliases must be a tuple of strings.")
        if any(not isinstance(alias, str) or not alias.strip() for alias in self.aliases):
            raise ValueError("aliases must contain non-empty strings.")


@dataclass(frozen=True, slots=True)
class CorrectionRule:
    """Immutable whole-word correction rule applied by the pure correct function."""

    source: str
    replacement: str

    def __post_init__(self) -> None:
        """Validate correction-rule text."""
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string.")
        if not isinstance(self.replacement, str):
            raise TypeError("replacement must be a string.")


@dataclass(frozen=True, slots=True)
class DiffSegment:
    """One immutable segment in a character-level text diff."""

    operation: Literal["equal", "insert", "delete"]
    text: str

    def __post_init__(self) -> None:
        """Validate the operation and segment text."""
        if self.operation not in ("equal", "insert", "delete"):
            raise ValueError("operation must be equal, insert, or delete.")
        if not isinstance(self.text, str):
            raise TypeError("text must be a string.")


@dataclass(frozen=True, slots=True)
class EntryData:
    """Immutable original entry data used as input to the hash-chain fold."""

    original_content: str
    timestamp: datetime
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Require immutable, typed values for all hash-covered data."""
        if not isinstance(self.original_content, str):
            raise TypeError("original_content must be a string.")
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime.")
        if not isinstance(self.metadata, tuple):
            raise TypeError("metadata must be a tuple of string pairs.")
        for item in self.metadata:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not all(isinstance(value, str) for value in item)
            ):
                raise TypeError("metadata must contain only string pairs.")


@dataclass(frozen=True, slots=True)
class ChainedEntry:
    """Immutable entry data plus its predecessor digest and current digest."""

    entry: EntryData
    previous_hash: str
    digest: str

    def __post_init__(self) -> None:
        """Validate the record's data and hash fields."""
        if not isinstance(self.entry, EntryData):
            raise TypeError("entry must be EntryData.")
        if not isinstance(self.previous_hash, str) or not isinstance(self.digest, str):
            raise TypeError("hash fields must be strings.")
