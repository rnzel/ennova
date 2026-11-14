# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Object-oriented service using a functional entry pipeline
from __future__ import annotations

from datetime import datetime

from app.domain.diary import (
    DiaryEntry,
    Entry,
    EntryRepository,
    InMemoryEntryRepository,
    LetterEntry,
    StoredEntry,
)
from app.domain.processing import (
    EntryData,
    PersonReference,
    extract_names,
    extract_topics,
    hash_entry,
    normalize,
    verify_hash_chain,
)
from app.errors import TamperDetected


class DiaryService:
    """Coordinate append-only diary storage and pure entry processing."""

    def __init__(self, repository: EntryRepository) -> None:
        """Create a service backed by an entry repository."""
        if not isinstance(repository, EntryRepository):
            raise TypeError("repository must implement EntryRepository.")
        self._repository = repository

    def add_diary_entry(
        self,
        owner_id: str,
        entry_id: str,
        original_content: str,
        timestamp: datetime,
        people: tuple[PersonReference, ...] = (),
    ) -> StoredEntry:
        """Create and append a diary entry using the caller-supplied timestamp."""
        self._validate_timestamp(timestamp)
        entry = DiaryEntry(entry_id, timestamp, original_content)
        return self._add_entry(owner_id, entry, people)

    def add_letter_entry(
        self,
        owner_id: str,
        entry_id: str,
        original_content: str,
        title: str,
        recipient: str,
        timestamp: datetime,
        people: tuple[PersonReference, ...] = (),
    ) -> StoredEntry:
        """Append a letter with an owner-unique title and policy-based release."""
        self._validate_timestamp(timestamp)
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("owner_id must be a non-empty string.")
        # The policy is the source of truth for release dates, not LetterEntry.release_date.
        entry = LetterEntry(
            entry_id,
            timestamp,
            original_content,
            title,
            recipient,
            release_date=None,
        )
        title_key = entry.title.casefold()
        if any(
            isinstance(record.entry, LetterEntry)
            and record.entry.title.casefold() == title_key
            for record in self._repository.list_for_owner(owner_id)
        ):
            raise ValueError(
                "A letter with this title already exists for this owner."
            )
        return self._add_entry(owner_id, entry, people)

    def get_entry(self, owner_id: str, entry_id: str) -> StoredEntry | None:
        """Read an entry without verifying its chain; access checks happen outside."""
        return self._repository.get(owner_id, entry_id)

    def list_entries(self, owner_id: str) -> tuple[StoredEntry, ...]:
        """Read an owner's entries without automatically verifying the chain."""
        return self._repository.list_for_owner(owner_id)

    def head_hash(self, owner_id: str) -> str | None:
        """Return the current chain head for an owner."""
        return self._repository.head_hash(owner_id)

    def verify(
        self, owner_id: str, expected_head: str | None = None
    ) -> bool:
        """Verify an authorized owner's full chain, optionally checking its head.

        Call only after access has been checked for every entry in the chain.
        Reads intentionally do not invoke this method automatically.
        """
        if expected_head is not None and not isinstance(expected_head, str):
            raise TypeError("expected_head must be a string or None.")

        records = self._repository.list_for_owner(owner_id)
        chain = tuple(record.chain_entry for record in records)
        verified = verify_hash_chain(chain)
        actual_head = chain[-1].digest if chain else None
        if expected_head is not None and expected_head != actual_head:
            raise TamperDetected(
                {"reason": "unexpected chain head", "expected": expected_head,
                 "actual": actual_head}
            )
        return verified

    def _add_entry(
        self,
        owner_id: str,
        entry: Entry,
        people: tuple[PersonReference, ...],
    ) -> StoredEntry:
        """Extract metadata, hash original data, and append one record."""
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("owner_id must be a non-empty string.")
        normalized_content = normalize(entry.original_content)
        names = extract_names(normalized_content, people)
        topics = extract_topics(normalized_content)

        metadata = [
            ("entry_id", entry.entry_id),
            ("owner_id", owner_id),
            ("kind", entry.kind),
        ]
        metadata.extend(("name", name) for name in names)
        metadata.extend(("topic", topic) for topic in topics)
        if isinstance(entry, LetterEntry):
            metadata.extend(
                (("title", entry.title), ("recipient", entry.recipient))
            )

        entry_data = EntryData(
            original_content=entry.original_content,
            timestamp=entry.created_at,
            metadata=tuple(metadata),
        )
        previous_hash = self._repository.head_hash(owner_id) or ""
        chain_entry = hash_entry(entry_data, previous_hash)
        record = StoredEntry(owner_id, entry, names, topics, chain_entry)
        self._repository.append(record)
        return record

    @staticmethod
    def _validate_timestamp(timestamp: datetime) -> None:
        """Require an aware timestamp supplied by the caller."""
        if not isinstance(timestamp, datetime):
            raise TypeError("timestamp must be a datetime.")
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware.")
