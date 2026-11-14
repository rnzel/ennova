# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Pure mapping from domain records to Prolog app facts
from __future__ import annotations

from app.domain.diary import LetterEntry, StoredEntry
from app.policy.access_bridge import AppFacts, EntryFact


def build_app_facts(
    owner_id: str,
    records: tuple[StoredEntry, ...],
    registered_people: tuple[str, ...],
    *,
    death_triggered: bool,
    policy_frozen: bool,
) -> AppFacts:
    """Build immutable F5 facts from one owner's stored entries."""
    if not isinstance(owner_id, str) or not owner_id.strip():
        raise ValueError("owner_id must be a non-empty string.")
    if not isinstance(records, tuple) or any(
        not isinstance(record, StoredEntry) for record in records
    ):
        raise TypeError("records must be a tuple of StoredEntry values.")
    if any(record.owner_id != owner_id for record in records):
        raise ValueError("records must belong to the requested owner.")
    if not isinstance(registered_people, tuple) or any(
        not isinstance(person, str) or not person.strip()
        for person in registered_people
    ):
        raise TypeError("registered_people must be a tuple of non-empty names.")
    if not isinstance(death_triggered, bool):
        raise TypeError("death_triggered must be a bool.")
    if not isinstance(policy_frozen, bool):
        raise TypeError("policy_frozen must be a bool.")

    return AppFacts(
        registered_people=tuple(person.casefold() for person in registered_people),
        death_triggered=death_triggered,
        policy_frozen=policy_frozen,
        entries=tuple(
            EntryFact(record.entry.entry_id, record.entry.kind) for record in records
        ),
        entry_mentions=tuple(
            (record.entry.entry_id, name.casefold())
            for record in records
            for name in record.names
        ),
        entry_tags=tuple(
            (record.entry.entry_id, topic.casefold())
            for record in records
            for topic in record.topics
        ),
        letters=tuple(
            (record.entry.entry_id, record.entry.title)
            for record in records
            if isinstance(record.entry, LetterEntry)
        ),
    )
