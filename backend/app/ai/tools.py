# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Permission-filtered grounded retrieval tools
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Mapping

from app.ai.prompts import LETTER_NOT_YET_MESSAGE, NEUTRAL_REPLY
from app.ai.summaries import SummaryStore
from app.domain.diary import LetterEntry, StoredEntry
from app.domain.processing import EntryData, hash_entry
from app.errors import AccessDenied, TamperDetected
from app.policy import AccessLevel, LetterStatus

_LEVEL_RANK = {"existence": 1, "summary": 2, "verbatim": 3}


@dataclass(frozen=True, slots=True)
class EntryView:
    """An entry payload restricted to the highest level Prolog permitted."""

    entry_id: str
    entry_date: date
    level: AccessLevel
    content: str


@dataclass(frozen=True, slots=True)
class LetterResult:
    """A permitted letter view or a safe backend-generated status message."""

    entry: EntryView | None = None
    message: str | None = None


@dataclass(frozen=True, slots=True)
class ToolContext:
    """Question-fixed identity and one pre-resolved Prolog permission batch."""

    owner_id: str
    asker: str
    today: date
    entries: tuple[StoredEntry, ...]
    permissions: Mapping[str, AccessLevel | None]
    verified_entry_ids: frozenset[str]
    letter_statuses: Mapping[str, LetterStatus]
    release_dates: Mapping[str, date]
    summaries: SummaryStore


def verify_entry(record: StoredEntry) -> bool:
    """Verify one entry after authorization, without traversing denied entries."""
    if not isinstance(record, StoredEntry):
        raise TypeError("record must be a StoredEntry.")

    entry = record.entry
    chain_entry = record.chain_entry
    hashed_entry = chain_entry.entry
    metadata = [
        ("entry_id", entry.entry_id),
        ("owner_id", record.owner_id),
        ("kind", entry.kind),
    ]
    metadata.extend(("name", name) for name in record.names)
    metadata.extend(("topic", topic) for topic in record.topics)
    if isinstance(entry, LetterEntry):
        metadata.extend(
            (("title", entry.title), ("recipient", entry.recipient))
        )

    expected_detail = {"entry_id": entry.entry_id}
    if (
        entry.original_content != hashed_entry.original_content
        or entry.created_at != hashed_entry.timestamp
        or Counter(metadata) != Counter(hashed_entry.metadata)
    ):
        raise TamperDetected(
            {"reason": "entry data differs from its hash record", **expected_detail}
        )

    current_data = EntryData(
        entry.original_content,
        entry.created_at,
        hashed_entry.metadata,
    )
    expected_hash = hash_entry(current_data, chain_entry.previous_hash).digest
    if expected_hash != chain_entry.digest:
        raise TamperDetected(
            {"reason": "entry digest mismatch", **expected_detail}
        )
    return True


def search_entries(query: str, context: ToolContext) -> tuple[EntryView, ...]:
    """Search only permitted, verified payloads, then score those candidates."""
    terms = tuple(term for term in query.casefold().split() if term)
    if not terms:
        return ()

    candidates: list[tuple[int, EntryView]] = []
    for record in context.entries:
        level = context.permissions.get(record.entry.entry_id)
        if level not in ("summary", "verbatim"):
            continue
        if record.entry.entry_id not in context.verified_entry_ids:
            continue
        view = _entry_view(record, level, context)
        if view is None:
            continue
        score = _score_text(terms, view.content)
        if score:
            candidates.append((score, view))
    candidates.sort(key=lambda item: (-item[0], item[1].entry_id))
    return tuple(view for _, view in candidates)


def get_entry(entry_id: str, context: ToolContext) -> EntryView | None:
    """Return one verified view at its resolved permission level."""
    record = next(
        (item for item in context.entries if item.entry.entry_id == entry_id),
        None,
    )
    if record is None:
        raise AccessDenied(detail={"entry_id": entry_id, "reason": "not found"})
    level = context.permissions.get(entry_id)
    if level is None:
        raise AccessDenied(detail={"entry_id": entry_id, "reason": "not allowed"})
    if entry_id not in context.verified_entry_ids:
        raise TamperDetected({"entry_id": entry_id, "reason": "unverified entry"})
    if level == "existence":
        return None
    return _entry_view(record, level, context)


def count_mentions(name: str, context: ToolContext) -> int | str:
    """Count only verified entries with existence permission; neutralize zero."""
    normalized_name = name.casefold()
    count = sum(
        1
        for record in context.entries
        if context.permissions.get(record.entry.entry_id) is not None
        and record.entry.entry_id in context.verified_entry_ids
        and any(mention.casefold() == normalized_name for mention in record.names)
    )
    return count if count else NEUTRAL_REPLY


def get_letter(title: str, context: ToolContext) -> LetterResult:
    """Return a permitted letter or a neutral/pre-release backend message."""
    matching = tuple(
        record
        for record in context.entries
        if isinstance(record.entry, LetterEntry)
        and record.entry.title.casefold() == title.casefold()
    )
    for record in matching:
        entry_id = record.entry.entry_id
        if (
            context.permissions.get(entry_id) == "verbatim"
            and entry_id in context.verified_entry_ids
        ):
            return LetterResult(_entry_view(record, "verbatim", context))

    matching_title = next(
        (
            known_title
            for known_title in context.letter_statuses
            if known_title.casefold() == title.casefold()
        ),
        None,
    )
    if (
        matching_title is not None
        and context.letter_statuses[matching_title] == "not_yet"
    ):
        release_date = context.release_dates.get(matching_title)
        if release_date is not None:
            return LetterResult(
                message=LETTER_NOT_YET_MESSAGE.format(
                    release_date=release_date.isoformat()
                )
            )
    return LetterResult(message=NEUTRAL_REPLY)


def _entry_view(
    record: StoredEntry,
    level: AccessLevel,
    context: ToolContext,
) -> EntryView | None:
    if level == "verbatim":
        content = record.entry.original_content
    elif level == "summary":
        summary = context.summaries.get(context.owner_id, record.entry.entry_id)
        if summary is None:
            return None
        content = summary.text
    else:
        return None
    return EntryView(
        record.entry.entry_id,
        record.entry.created_at.date(),
        level,
        content,
    )


def _score_text(terms: tuple[str, ...], content: str) -> int:
    """Return a deterministic term-match score for already permitted content."""
    folded_content = content.casefold()
    return sum(1 for term in terms if term in folded_content)


__all__ = [
    "EntryView",
    "LetterResult",
    "ToolContext",
    "count_mentions",
    "get_entry",
    "get_letter",
    "search_entries",
    "verify_entry",
]
