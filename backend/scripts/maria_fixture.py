"""Reusable fictional Lola/Maria diary records for the demo and backend tests."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from app.domain.diary import InMemoryEntryRepository, StoredEntry
from app.domain.processing import PersonReference
from app.policy import AppFacts, ReleaseLetter, parse
from app.services.access_facts import build_app_facts
from app.services.diary_service import DiaryService

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
POLICY_PATH = PROJECT_DIR / "docs" / "grammar" / "sample_maria.policy"
OWNER_ID = "owner-lola"
MARIA_ID = "beneficiary-maria"
NORA_ID = "beneficiary-nora"
LETTER_TITLE = "To my daughter"
LETTER_RECIPIENT = "Maria"
LETTER_ENTRY_ID = "e_letter"


@dataclass(frozen=True)
class DiarySeed:
    entry_id: str
    created: date
    content: str


DIARY_SEEDS: tuple[DiarySeed, ...] = (
    DiarySeed("e_maria", date(2017, 3, 12), "Lola remembers a lantern walk beside the garden with [[Maria]]."),
    DiarySeed("e_family", date(2018, 7, 21), "The fictional family shared soup with [[Maria]] after the rain. #family"),
    DiarySeed("e_family_2", date(2019, 11, 3), "A quiet family supper at home brought everyone a little closer. #family"),
    DiarySeed("e_business", date(2020, 2, 18), "Lola reviewed the orchard shop ledger and planned a new display. #business"),
    DiarySeed("e_garden", date(2017, 9, 5), "The blue beans climbed the trellis beside the small kitchen garden. #garden"),
    DiarySeed("e_shop_sign", date(2018, 1, 27), "A hand-painted sign made the fictional corner shop easier to find. #business"),
    DiarySeed("e_family_3", date(2019, 5, 16), "The cousins invented a paper boat race along the garden path. #family"),
    DiarySeed("e_harvest", date(2020, 10, 8), "Neighbors helped sort the orchard harvest into baskets for the shop. #business"),
    DiarySeed("e_family_4", date(2021, 4, 2), "We celebrated a small birthday with citrus cake and hand-written cards. #family"),
    DiarySeed("e_repairs", date(2021, 12, 14), "Lola compared wooden shelf plans before repairing the shop storeroom. #business"),
    DiarySeed("e_family_5", date(2022, 6, 30), "A rainy afternoon turned into a board-game tournament at home. #family"),
    DiarySeed("e_supplies", date(2022, 9, 19), "The shop tested a reusable-paper wrapping idea for its parcels. #business"),
    DiarySeed("e_family_6", date(2023, 2, 11), "The family took a slow picnic beside the invented Glassbird Lake. #family"),
    DiarySeed("e_market", date(2023, 8, 23), "Lola reserved a stall at the fictional Lantern Market for fruit preserves. #business"),
    DiarySeed("e_family_7", date(2024, 1, 6), "A shared recipe notebook gathered everyone's favorite winter meals. #family"),
    DiarySeed("e_orchard", date(2024, 5, 29), "The orchard shop added a crate exchange for nearby growers. #business"),
    DiarySeed("e_family_8", date(2025, 3, 17), "The children built a cardboard observatory and named the stars themselves. #family"),
    DiarySeed("e_family_9", date(2025, 10, 4), "A family walk through the fictional Fernbridge park ended with warm tea. #family"),
    DiarySeed("e_family_10", date(2026, 4, 13), "We planted a small row of herbs and labeled each pot together. #family"),
    DiarySeed("e_family_11", date(2026, 11, 14), "The fictional family shared a late breakfast and planned another reunion. #family"),
)

LETTER_CONTENT = (
    "My dearest daughter, remember this small story about kindness. "
    "When the lantern went out on the old garden path, our neighbors brought "
    "their lights and walked beside us. I hope you keep making room for "
    "people, patience, and ordinary acts of care. With love, Lola."
)


@dataclass(frozen=True)
class MariaFixture:
    owner_id: str
    repository: InMemoryEntryRepository
    service: DiaryService
    records: tuple[StoredEntry, ...]
    app_facts: AppFacts
    people: tuple[PersonReference, ...]
    policy_source: str
    release_date: date


def _letter_release_date(policy_source: str) -> date:
    policy = parse(policy_source)
    dates = tuple(
        statement.release_date
        for statement in policy.statements
        if isinstance(statement, ReleaseLetter)
        and statement.title == LETTER_TITLE
        and statement.person.casefold() == "maria"
    )
    if len(dates) != 1:
        raise ValueError("The Maria sample policy must define one daughter-letter release date.")
    return dates[0]


def build_maria_fixture() -> MariaFixture:
    """Build Lola's deterministic diary and derive letter metadata from policy."""
    policy_source = POLICY_PATH.read_text(encoding="utf-8")
    release_date = _letter_release_date(policy_source)
    repository = InMemoryEntryRepository()
    service = DiaryService(repository)
    people = (
        PersonReference(MARIA_ID, LETTER_RECIPIENT),
        PersonReference(NORA_ID, "Nora"),
    )
    records = tuple(
        service.add_diary_entry(
            OWNER_ID,
            seed.entry_id,
            seed.content,
            datetime(
                seed.created.year,
                seed.created.month,
                seed.created.day,
                12,
                tzinfo=timezone.utc,
            ),
            people,
        )
        for seed in DIARY_SEEDS
    ) + (
        service.add_letter_entry(
            OWNER_ID,
            LETTER_ENTRY_ID,
            LETTER_CONTENT,
            LETTER_TITLE,
            LETTER_RECIPIENT,
            datetime(2026, 11, 15, 9, tzinfo=timezone.utc),
            people,
            release_date=release_date,
        ),
    )
    app_facts = build_app_facts(
        OWNER_ID,
        records,
        (LETTER_RECIPIENT, "Nora"),
        death_triggered=True,
        policy_frozen=True,
    )
    return MariaFixture(
        OWNER_ID,
        repository,
        service,
        records,
        app_facts,
        people,
        policy_source,
        release_date,
    )


__all__ = [
    "DIARY_SEEDS",
    "LETTER_CONTENT",
    "LETTER_ENTRY_ID",
    "LETTER_RECIPIENT",
    "LETTER_TITLE",
    "MariaFixture",
    "OWNER_ID",
    "POLICY_PATH",
    "build_maria_fixture",
]
