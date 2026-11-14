# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Functional entry processing
from __future__ import annotations

import difflib
import hashlib
import json
import re
import unicodedata
from datetime import datetime
from functools import reduce

from .exceptions import AmbiguousName, TamperDetected
from .models import (
    ChainedEntry,
    CorrectionRule,
    DiffSegment,
    EntryData,
    PersonReference,
)

_NAME_LINK_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")
_TOPIC_PATTERN = re.compile(r"(?<!\w)#([\w][\w-]*)", re.UNICODE)
_GENESIS_HASH = ""


def normalize(text: str) -> str:
    """Normalize Unicode composition and line endings without changing other spacing."""
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    line_normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", line_normalized)


def _person_aliases(
    people: tuple[PersonReference, ...],
) -> dict[str, dict[str, str]]:
    """Map each case-folded canonical name or alias to its possible people."""
    aliases: dict[str, dict[str, str]] = {}
    for person in people:
        if not isinstance(person, PersonReference):
            raise TypeError("people must contain only PersonReference values.")
        for alias in (person.canonical_name, *person.aliases):
            key = alias.casefold()
            aliases.setdefault(key, {})[person.person_id] = person.canonical_name
    return aliases


def _resolve_name(
    name: str, aliases: dict[str, dict[str, str]]
) -> str:
    """Resolve a known alias, raising rather than guessing on ambiguity."""
    matches = aliases.get(name.casefold(), {})
    if len(matches) > 1:
        raise AmbiguousName(
            {"name": name, "candidates": tuple(matches.values())}
        )
    if matches:
        return next(iter(matches.values()))
    return name


def extract_names(
    text: str, people: tuple[PersonReference, ...] = ()
) -> tuple[str, ...]:
    """Extract linked and known plain names in first-occurrence order."""
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    if not isinstance(people, tuple):
        raise TypeError("people must be a tuple of PersonReference values.")

    aliases = _person_aliases(people)
    links = tuple(_NAME_LINK_PATTERN.finditer(text))
    found = [
        (
            match.start(),
            _resolve_name(match.group(1).strip(), aliases),
            (match.start(), match.end()),
        )
        for match in links
    ]

    if aliases:
        alias_patterns = sorted(aliases, key=lambda value: (-len(value), value))
        pattern = re.compile(
            r"(?<!\w)(?:"
            + "|".join(re.escape(alias) for alias in alias_patterns)
            + r")(?!\w)",
            re.IGNORECASE | re.UNICODE,
        )
        link_spans = tuple((match.start(), match.end()) for match in links)
        for match in pattern.finditer(text):
            if any(start < match.end() and match.start() < end for start, end in link_spans):
                continue
            name = match.group()
            found.append(
                (match.start(), _resolve_name(name, aliases), (match.start(), match.end()))
            )

    ordered_names = sorted(found, key=lambda item: item[0])
    results: list[str] = []
    seen: set[str] = set()
    for _, name, _ in ordered_names:
        key = name.casefold()
        if key not in seen:
            results.append(name)
            seen.add(key)
    return tuple(results)


def extract_topics(text: str) -> tuple[str, ...]:
    """Extract case-folded hashtags in first-occurrence order without duplicates."""
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    topics: list[str] = []
    seen: set[str] = set()
    for match in _TOPIC_PATTERN.finditer(text):
        topic = match.group(1).casefold()
        if topic not in seen:
            topics.append(topic)
            seen.add(topic)
    return tuple(topics)


def _preserve_case(source: str, replacement: str) -> str:
    """Apply the source token's basic capitalization pattern to a replacement."""
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def correct(text: str, rules: tuple[CorrectionRule, ...]) -> str:
    """Apply caller-supplied whole-word corrections in order without mutating input."""
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    if not isinstance(rules, tuple) or any(
        not isinstance(rule, CorrectionRule) for rule in rules
    ):
        raise TypeError("rules must be a tuple of CorrectionRule values.")

    corrected = text
    for rule in rules:
        pattern = re.compile(
            r"(?<!\w)" + re.escape(rule.source) + r"(?!\w)",
            re.IGNORECASE | re.UNICODE,
        )
        corrected = pattern.sub(
            lambda match: _preserve_case(match.group(), rule.replacement), corrected
        )
    return corrected


def diff(before: str, after: str) -> tuple[DiffSegment, ...]:
    """Return deterministic character-level equal, delete, and insert segments."""
    if not isinstance(before, str) or not isinstance(after, str):
        raise TypeError("before and after must be strings.")

    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    segments: list[DiffSegment] = []
    for operation, before_start, before_end, after_start, after_end in matcher.get_opcodes():
        if operation == "equal":
            segments.append(DiffSegment("equal", before[before_start:before_end]))
        elif operation in ("delete", "replace"):
            segments.append(DiffSegment("delete", before[before_start:before_end]))
            if operation == "replace":
                segments.append(DiffSegment("insert", after[after_start:after_end]))
        else:
            segments.append(DiffSegment("insert", after[after_start:after_end]))
    return tuple(segments)


def hash_entry(entry: EntryData, previous_hash: str) -> ChainedEntry:
    """Hash original content, timestamp, canonical metadata, and predecessor with SHA-256."""
    if not isinstance(entry, EntryData):
        raise TypeError("entry must be EntryData.")
    if not isinstance(previous_hash, str):
        raise TypeError("previous_hash must be a string.")

    payload = {
        "metadata": sorted(entry.metadata),
        "original_content": entry.original_content,
        "previous_hash": previous_hash,
        "timestamp": entry.timestamp.isoformat(),
    }
    canonical_payload = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = hashlib.sha256(canonical_payload).hexdigest()
    return ChainedEntry(entry, previous_hash, digest)


def _append_to_chain(
    chain: tuple[ChainedEntry, ...], entry: EntryData
) -> tuple[ChainedEntry, ...]:
    """Append one hash link as an immutable tuple fold step."""
    previous_hash = chain[-1].digest if chain else _GENESIS_HASH
    return (*chain, hash_entry(entry, previous_hash))


def hash_chain(entries: tuple[EntryData, ...]) -> tuple[ChainedEntry, ...]:
    """Build an append-ordered SHA-256 chain by folding immutable entry data."""
    if not isinstance(entries, tuple):
        raise TypeError("entries must be a tuple of EntryData values.")
    return reduce(_append_to_chain, entries, ())


def verify_hash_chain(chain: tuple[ChainedEntry, ...]) -> bool:
    """Verify every entry digest and predecessor link, raising on tampering."""
    if not isinstance(chain, tuple):
        raise TypeError("chain must be a tuple of ChainedEntry values.")

    previous_hash = _GENESIS_HASH
    for index, chained_entry in enumerate(chain):
        if not isinstance(chained_entry, ChainedEntry):
            raise TypeError("chain must contain only ChainedEntry values.")
        if chained_entry.previous_hash != previous_hash:
            raise TamperDetected(
                {"reason": "hash-chain link mismatch", "position": index}
            )
        expected = hash_entry(chained_entry.entry, previous_hash)
        if chained_entry.digest != expected.digest:
            raise TamperDetected(
                {"reason": "entry hash mismatch", "position": index}
            )
        previous_hash = chained_entry.digest
    return True
