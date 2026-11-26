# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Permission-filtered grounded retrieval tools
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
import re
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
    stopwords = {
        "a",
        "about",
        "did",
        "do",
        "does",
        "he",
        "her",
        "his",
        "i",
        "in",
        "is",
        "it",
        "me",
        "my",
        "of",
        "she",
        "tell",
        "the",
        "to",
        "what",
        "with",
        "write",
        "wrote",
    }
    terms = tuple(
        term.strip(".,!?;:\"'")
        for term in query.casefold().split()
        if term.strip(".,!?;:\"'").casefold() not in stopwords
        and term.strip(".,!?;:\"'")
    )
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


def search_owner_entries(
    query: str,
    owner_id: str,
    entries: tuple[StoredEntry, ...],
    *,
    today: date,
    limit: int = 6,
    date_context: str | None = None,
) -> tuple[EntryView, ...]:
    """Rank verified owner records using diary text, metadata, and date cues.

    This local retrieval path is deliberately separate from beneficiary
    ``search_entries``: it has no Prolog permission map and accepts only the
    authenticated owner's already verified records.
    """
    if not isinstance(query, str) or not isinstance(owner_id, str):
        return ()
    if not isinstance(entries, tuple) or not isinstance(today, date):
        return ()
    if not isinstance(limit, int) or limit < 1:
        return ()

    tokens = _owner_query_tokens(query)
    date_query = date_context if isinstance(date_context, str) else query
    requested_years = tuple(re.findall(r"\b(?:19|20)\d{2}\b", date_query))
    has_last_year = "last year" in date_query.casefold()
    if not tokens and not requested_years and not has_last_year:
        return ()
    target_years = {requested_years[-1]} if requested_years else set()
    if has_last_year:
        target_years.add(str(today.year - 1))

    scored: list[tuple[int, date, str, EntryView]] = []
    for record in entries:
        if record.owner_id != owner_id:
            continue
        entry = record.entry
        entry_date = entry.created_at.date()
        if target_years and str(entry_date.year) not in target_years:
            continue

        content_tokens = set(_owner_query_tokens(entry.original_content))
        metadata_tokens = set(
            _owner_query_tokens(" ".join((*record.names, *record.topics)))
        )
        score = sum(
            (2 if token in content_tokens else 0)
            + (3 if token in metadata_tokens else 0)
            for token in tokens
        )
        if not tokens and target_years:
            score = 1
        if score <= 0:
            continue
        scored.append(
            (
                score,
                entry_date,
                entry.entry_id,
                EntryView(entry.entry_id, entry_date, "verbatim", entry.original_content),
            )
        )

    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    return tuple(item[3] for item in scored[:limit])


_OWNER_STOPWORDS = frozenset(
    {
        "a", "about", "an", "and", "are", "at", "did", "do", "does",
        "for", "from", "i", "in", "into", "is", "it", "me", "my", "of",
        "during", "last", "on", "or", "that", "the", "their", "them", "there", "these",
        "they", "this", "to", "was", "were", "what", "when", "where",
        "which", "who", "summarize", "summary", "diary", "with", "would", "write", "wrote", "year", "your",
    }
)
_OWNER_SYNONYM_GROUPS = (
    frozenset({"happy", "happiest", "happiness", "joy", "joyful", "glad", "delight", "wonderful", "memorable", "best"}),
    frozenset({"challenge", "challenging", "hard", "hardship", "difficult", "difficulty", "struggle", "obstacle"}),
    frozenset({"goal", "goals", "career", "ambition", "aspiration", "future", "profession"}),
    frozenset({"lesson", "lessons", "learn", "learned", "realize", "realized", "taught", "experience"}),
)


def _owner_query_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for token in re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE):
        if token in _OWNER_STOPWORDS or token.isdigit():
            continue
        token = _normalize_owner_token(token)
        tokens.append(token)
        for group in _OWNER_SYNONYM_GROUPS:
            if token in group:
                tokens.extend(sorted(_normalize_owner_token(item) for item in group if item != token))
                break
    return tuple(dict.fromkeys(tokens))


def _normalize_owner_token(token: str) -> str:
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        stem = token[:-2]
        if stem.endswith(("gl", "z", "nc")):
            return stem + "e"
        return stem
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


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
        if (
            summary is None
            or summary.source_digest != record.chain_entry.digest
        ):
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
    "search_owner_entries",
    "verify_entry",
]
