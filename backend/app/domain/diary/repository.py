# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Object-oriented append-only entry repository
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.processing import ChainedEntry

from .model import Entry


@dataclass(frozen=True, slots=True)
class StoredEntry:
    """An original entry, its extracted metadata, and its hash-chain record."""

    owner_id: str
    entry: Entry
    names: tuple[str, ...]
    topics: tuple[str, ...]
    chain_entry: ChainedEntry

    def __post_init__(self) -> None:
        """Validate the immutable record and bind its hash to stored identity."""
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id must be a non-empty string.")
        if not isinstance(self.entry, Entry):
            raise TypeError("entry must be an Entry.")
        if not isinstance(self.chain_entry, ChainedEntry):
            raise TypeError("chain_entry must be a ChainedEntry.")
        if not isinstance(self.names, tuple) or not all(
            isinstance(name, str) for name in self.names
        ):
            raise TypeError("names must be a tuple of strings.")
        if not isinstance(self.topics, tuple) or not all(
            isinstance(topic, str) for topic in self.topics
        ):
            raise TypeError("topics must be a tuple of strings.")

        hash_data = self.chain_entry.entry
        if hash_data.original_content != self.entry.original_content:
            raise ValueError("The hash record must contain the original entry text.")
        if hash_data.timestamp != self.entry.created_at:
            raise ValueError("The hash timestamp must match Entry.created_at.")
        if ("owner_id", self.owner_id) not in hash_data.metadata:
            raise ValueError("The hash metadata must include owner_id.")
        if ("entry_id", self.entry.entry_id) not in hash_data.metadata:
            raise ValueError("The hash metadata must include entry_id.")


class EntryRepository(ABC):
    """Interface for owner-scoped, append-only entry storage."""

    @abstractmethod
    def append(self, record: StoredEntry) -> None:
        """Append a record, rejecting duplicate identifiers for its owner."""

    @abstractmethod
    def get(self, owner_id: str, entry_id: str) -> StoredEntry | None:
        """Return one owner's entry by identifier, or None when absent."""

    @abstractmethod
    def list_for_owner(self, owner_id: str) -> tuple[StoredEntry, ...]:
        """Return an immutable snapshot of one owner's entries in append order."""

    @abstractmethod
    def head_hash(self, owner_id: str) -> str | None:
        """Return the last digest for an owner, or None for an empty chain."""


class InMemoryEntryRepository(EntryRepository):
    """Owner-scoped in-memory implementation with append-only operations."""

    __slots__ = ("_entries", "_entry_ids")

    def __init__(self) -> None:
        """Create empty entry and identity indexes."""
        self._entries: dict[str, list[StoredEntry]] = {}
        self._entry_ids: dict[str, set[str]] = {}

    def append(self, record: StoredEntry) -> None:
        """Append a record after validating uniqueness and chain continuity."""
        if not isinstance(record, StoredEntry):
            raise TypeError("record must be a StoredEntry.")

        owner_entries = self._entries.get(record.owner_id, [])
        owner_ids = self._entry_ids.get(record.owner_id, set())
        if record.entry.entry_id in owner_ids:
            raise ValueError(f"Entry ID already exists: {record.entry.entry_id}")

        expected_previous = (
            owner_entries[-1].chain_entry.digest if owner_entries else ""
        )
        if record.chain_entry.previous_hash != expected_previous:
            raise ValueError("The hash record does not extend this owner's chain.")

        # This in-memory append is not thread-safe; a database implementation must
        # atomically read the last hash and insert the next record.
        self._entries.setdefault(record.owner_id, []).append(record)
        self._entry_ids.setdefault(record.owner_id, set()).add(record.entry.entry_id)

    def get(self, owner_id: str, entry_id: str) -> StoredEntry | None:
        """Return an entry only from the requested owner's collection."""
        for record in self._entries.get(owner_id, ()):
            if record.entry.entry_id == entry_id:
                return record
        return None

    def list_for_owner(self, owner_id: str) -> tuple[StoredEntry, ...]:
        """Return an immutable snapshot of the requested owner's entries."""
        return tuple(self._entries.get(owner_id, ()))

    def head_hash(self, owner_id: str) -> str | None:
        """Return the latest chain digest for this owner, if one exists."""
        owner_entries = self._entries.get(owner_id, ())
        return owner_entries[-1].chain_entry.digest if owner_entries else None
