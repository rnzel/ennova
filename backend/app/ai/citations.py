# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Backend verification of model citation IDs
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping

from app.domain.diary import StoredEntry


@dataclass(frozen=True, slots=True)
class Citation:
    """A verified entry identifier paired with its stored calendar date."""

    entry_id: str
    entry_date: date


@dataclass(frozen=True, slots=True)
class GroundedResponse:
    """User-facing text with citations validated by the backend."""

    text: str
    citations: tuple[Citation, ...] = ()


def attach_citations(
    text: str,
    citation_ids: tuple[str, ...],
    permitted_entries: Mapping[str, StoredEntry],
) -> GroundedResponse:
    """Drop unpermitted IDs and attach dates from the stored entries."""
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    if not isinstance(citation_ids, tuple):
        raise TypeError("citation_ids must be a tuple.")

    citations: list[Citation] = []
    seen: set[str] = set()
    for entry_id in citation_ids:
        if not isinstance(entry_id, str) or entry_id in seen:
            continue
        record = permitted_entries.get(entry_id)
        if record is None or record.entry.entry_id != entry_id:
            continue
        seen.add(entry_id)
        citations.append(
            Citation(entry_id, record.entry.created_at.date())
        )
    return GroundedResponse(text, tuple(citations))
