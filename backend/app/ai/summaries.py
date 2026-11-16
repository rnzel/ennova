# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Summary test doubles and in-memory derived-summary storage
from __future__ import annotations

from app.ai.model_summaries import (
    ModelSummarizer,
    SummaryArtifact,
    SummaryStore,
    Summarizer,
    store_derived_summary,
)
from app.domain.diary import StoredEntry


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
        if (
            not artifact.owner_id.strip()
            or not artifact.entry_id.strip()
            or not artifact.source_digest.strip()
        ):
            raise ValueError(
                "summary owner_id, entry_id, and source_digest must be non-empty."
            )
        if not artifact.text.strip():
            raise ValueError("summary text must be non-empty.")
        self._summaries[(artifact.owner_id, artifact.entry_id)] = artifact


__all__ = [
    "FakeSummarizer",
    "InMemorySummaryStore",
    "ModelSummarizer",
    "SummaryArtifact",
    "SummaryStore",
    "Summarizer",
    "store_derived_summary",
]
