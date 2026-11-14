# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Derived summaries stored outside the original-entry hash chain
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.diary import StoredEntry


@dataclass(frozen=True, slots=True)
class SummaryArtifact:
    """A derived, replaceable summary separate from the append-only entry chain."""

    owner_id: str
    entry_id: str
    text: str


class Summarizer(Protocol):
    """Interface that derives a summary without changing its original entry."""

    def summarize(self, record: StoredEntry) -> str:
        """Return a derived summary for one stored entry."""


class SummaryStore(Protocol):
    """Interface for derived summaries stored outside the entry hash chain."""

    def get(self, owner_id: str, entry_id: str) -> SummaryArtifact | None:
        """Return a stored summary or None when one has not been produced."""

    def put(self, artifact: SummaryArtifact) -> None:
        """Store or replace a derived summary artifact."""


class FakeSummarizer:
    """Deterministic summary test double based only on extracted metadata."""

    def summarize(self, record: StoredEntry) -> str:
        """Describe indexed topics and names without copying original wording."""
        if not isinstance(record, StoredEntry):
            raise TypeError("record must be a StoredEntry.")
        parts: list[str] = []
        if record.topics:
            parts.append("Topics: " + ", ".join(record.topics) + ".")
        if record.names:
            parts.append(
                "People mentioned: "
                + ", ".join(name.casefold() for name in record.names)
                + "."
            )
        return " ".join(parts) if parts else "No indexed topics or names."


class InMemorySummaryStore:
    """In-memory map of derived summaries that is not part of the hash chain."""

    def __init__(self) -> None:
        """Create an empty owner-and-entry keyed summary map."""
        self._summaries: dict[tuple[str, str], SummaryArtifact] = {}

    def get(self, owner_id: str, entry_id: str) -> SummaryArtifact | None:
        """Return the requested derived summary without accessing original text."""
        return self._summaries.get((owner_id, entry_id))

    def put(self, artifact: SummaryArtifact) -> None:
        """Store a derived summary without modifying its entry or hash record."""
        if not isinstance(artifact, SummaryArtifact):
            raise TypeError("artifact must be a SummaryArtifact.")
        if not artifact.owner_id.strip() or not artifact.entry_id.strip():
            raise ValueError("summary owner_id and entry_id must be non-empty.")
        if not artifact.text.strip():
            raise ValueError("summary text must be non-empty.")
        self._summaries[(artifact.owner_id, artifact.entry_id)] = artifact


def store_derived_summary(
    record: StoredEntry,
    summarizer: Summarizer,
    store: SummaryStore,
) -> SummaryArtifact:
    """Create and store a summary artifact outside the original hash chain."""
    if not isinstance(record, StoredEntry):
        raise TypeError("record must be a StoredEntry.")
    text = summarizer.summarize(record)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("summarizer must return non-empty text.")
    artifact = SummaryArtifact(record.owner_id, record.entry.entry_id, text)
    store.put(artifact)
    return artifact
