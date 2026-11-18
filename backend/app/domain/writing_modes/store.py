# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Object-oriented append-only derived-version storage
from __future__ import annotations

from dataclasses import dataclass

from app.domain.diary import StoredEntry

from .models import DerivedVersion


@dataclass(frozen=True, slots=True)
class StoredDerivedVersion:
    """One append-only derived version with its caller-supplied sequence."""

    sequence_number: int
    version: DerivedVersion


class InMemoryDerivedVersionStore:
    """Append-only store that never changes the source hash chain."""

    def __init__(self) -> None:
        self._versions: list[StoredDerivedVersion] = []

    def append(
        self, version: DerivedVersion, sequence_number: int
    ) -> StoredDerivedVersion:
        """Append a version with a strictly increasing caller-supplied sequence."""
        if not isinstance(version, DerivedVersion):
            raise TypeError("version must be a DerivedVersion.")
        if not isinstance(sequence_number, int) or sequence_number < 0:
            raise ValueError("sequence_number must be a non-negative integer.")
        if self._versions and sequence_number <= self._versions[-1].sequence_number:
            raise ValueError("sequence_number must increase for append.")
        stored = StoredDerivedVersion(sequence_number, version)
        self._versions.append(stored)
        return stored

    def list_all(self) -> tuple[StoredDerivedVersion, ...]:
        """Return an immutable append-order snapshot."""
        return tuple(self._versions)

    @staticmethod
    def matches_current(version: DerivedVersion, entry: StoredEntry) -> bool:
        """Report whether a derived version still matches the entry digest."""
        if not isinstance(version, DerivedVersion):
            raise TypeError("version must be a DerivedVersion.")
        if not isinstance(entry, StoredEntry):
            raise TypeError("entry must be a StoredEntry.")
        return (
            version.source_entry_id == entry.entry.entry_id
            and version.source_digest == entry.chain_entry.digest
        )
