# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Entry-store and service integration tests
from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.domain.diary import (
    DiaryEntry,
    EntryRepository,
    InMemoryEntryRepository,
    LetterEntry,
    StoredEntry,
)
from app.domain.processing import PersonReference
from app.errors import AmbiguousName, TamperDetected
from app.policy import (
    AccessRequest,
    AppFacts,
    EntryFact,
    PrologAccessBridge,
    parse,
)
from app.services import DiaryService, build_app_facts

ROOT = Path(__file__).parents[2]
MARIA_POLICY_PATH = ROOT / "docs" / "grammar" / "sample_maria.policy"
ACCESS_TABLE_PATH = ROOT / "docs" / "access-test-table.md"


@dataclass(frozen=True)
class MariaStoreSample:
    """Fictional Maria scenario with expected mention, tag, and access outcomes."""

    owner_id: str
    repository: InMemoryEntryRepository
    service: DiaryService
    records: tuple[StoredEntry, ...]
    app_facts: AppFacts
    expected_maria_mentions: tuple[str, ...]
    family_without_maria: str
    entries_without_maria_link: tuple[str, ...]
    registered_person_without_protocol: str


@pytest.fixture
def maria_store_sample() -> MariaStoreSample:
    """Create Lola's fictional diary for the Maria policy acceptance scenario.

    Expected: e_maria and e_family mention Maria; e_family_2 is tagged family
    but does not mention her; e_business and e_letter contain no [[maria]] link;
    Nora is registered but has no protocol in the sample policy.
    """
    owner_id = "owner-lola"
    repository = InMemoryEntryRepository()
    service = DiaryService(repository)
    people = (
        PersonReference("beneficiary-maria", "Maria"),
        PersonReference("beneficiary-nora", "Nora"),
    )
    timestamps = tuple(
        datetime(2026, 11, 14, hour, tzinfo=timezone.utc)
        for hour in range(9, 14)
    )
    records = (
        service.add_diary_entry(
            owner_id,
            "e_maria",
            "Lola remembers visiting [[Maria]] beside the garden.",
            timestamps[0],
            people,
        ),
        service.add_diary_entry(
            owner_id,
            "e_family",
            "The fictional family shared soup with [[Maria]]. #family",
            timestamps[1],
            people,
        ),
        service.add_diary_entry(
            owner_id,
            "e_family_2",
            "A quiet family supper at home. #family",
            timestamps[2],
            people,
        ),
        service.add_diary_entry(
            owner_id,
            "e_business",
            "Lola reviewed the orchard shop ledger. #business",
            timestamps[3],
            people,
        ),
        service.add_letter_entry(
            owner_id,
            "e_letter",
            "My dearest daughter, remember this small story about kindness.",
            "To my daughter",
            "Maria",
            timestamps[4],
            people,
        ),
    )
    app_facts = build_app_facts(
        owner_id,
        records,
        ("Maria", "Nora"),
        death_triggered=True,
        policy_frozen=True,
    )
    return MariaStoreSample(
        owner_id=owner_id,
        repository=repository,
        service=service,
        records=records,
        app_facts=app_facts,
        expected_maria_mentions=("e_maria", "e_family"),
        family_without_maria="e_family_2",
        entries_without_maria_link=("e_business", "e_letter"),
        registered_person_without_protocol="nora",
    )


def _maria_acceptance_rows() -> tuple[dict[str, str], ...]:
    """Read the six executable Maria acceptance rows from the access table."""
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in ACCESS_TABLE_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        row = dict(zip(header, cells))
        if row["Scenario"] == "maria_acceptance":
            rows.append(row)
    return tuple(rows)


def test_repository_is_append_only_and_reads_are_owner_scoped(
    maria_store_sample: MariaStoreSample,
):
    repository = maria_store_sample.repository
    first = maria_store_sample.records[0]

    assert isinstance(repository, EntryRepository)
    assert repository.get(maria_store_sample.owner_id, first.entry.entry_id) is first
    assert repository.get("another-owner", first.entry.entry_id) is None
    assert repository.list_for_owner(maria_store_sample.owner_id) == (
        maria_store_sample.records
    )
    assert not hasattr(repository, "update")
    assert not hasattr(repository, "delete")
    assert not hasattr(repository, "remove")
    with pytest.raises(ValueError, match="Entry ID already exists"):
        repository.append(first)


def test_sample_documents_expected_mentions_tags_and_policy_recipient(
    maria_store_sample: MariaStoreSample,
):
    sample = maria_store_sample
    by_id = {record.entry.entry_id: record for record in sample.records}
    actual_mentions = tuple(
        entry_id
        for entry_id, name in sample.app_facts.entry_mentions
        if name == "maria"
    )

    assert actual_mentions == sample.expected_maria_mentions
    family_record = by_id[sample.family_without_maria]
    assert "family" in family_record.topics
    assert "maria" not in tuple(name.casefold() for name in family_record.names)
    for entry_id in sample.entries_without_maria_link:
        assert "[[maria]]" not in by_id[entry_id].entry.original_content.casefold()
    assert "business" in by_id["e_business"].topics

    letter = by_id["e_letter"].entry
    assert isinstance(letter, LetterEntry)
    assert letter.title == "To my daughter"
    assert letter.recipient == "Maria"
    assert letter.release_date is None
    assert sample.app_facts.letters == (("e_letter", "To my daughter"),)
    assert "nora" in sample.app_facts.registered_people
    assert "protocol nora:" not in MARIA_POLICY_PATH.read_text(
        encoding="utf-8"
    ).casefold()


def test_service_keeps_original_text_and_binds_hash_to_owner_entry_and_timestamp():
    repository = InMemoryEntryRepository()
    service = DiaryService(repository)
    timestamp = datetime(2026, 11, 14, 10, tzinfo=timezone.utc)
    original = "A fictional note for [[Maria]]."

    record = service.add_diary_entry(
        "owner-lola", "entry-1", original, timestamp
    )

    assert isinstance(record.entry, DiaryEntry)
    assert record.entry.original_content == original
    assert record.entry.created_at == timestamp
    assert record.chain_entry.entry.original_content == original
    assert record.chain_entry.entry.timestamp == record.entry.created_at
    assert ("owner_id", "owner-lola") in record.chain_entry.entry.metadata
    assert ("entry_id", "entry-1") in record.chain_entry.entry.metadata
    assert record.names == ("Maria",)
    assert not hasattr(record, "corrected_content")


def test_duplicate_letter_titles_are_rejected_before_hash_chain_changes(
    swipl_executable: str,
):
    repository = InMemoryEntryRepository()
    service = DiaryService(repository)
    owner_id = "owner-lola"
    first = service.add_letter_entry(
        owner_id,
        "letter-one",
        "A fictional note for Maria.",
        "To Maria",
        "Maria",
        datetime(2026, 11, 14, 10, tzinfo=timezone.utc),
    )
    records_before = service.list_entries(owner_id)
    head_before = service.head_hash(owner_id)

    with pytest.raises(ValueError, match="title already exists"):
        service.add_letter_entry(
            owner_id,
            "letter-two",
            "A second fictional note for Maria.",
            "tO mArIa",
            "Maria",
            datetime(2026, 11, 14, 11, tzinfo=timezone.utc),
        )

    assert service.list_entries(owner_id) == records_before == (first,)
    assert service.head_hash(owner_id) == head_before
    assert service.verify(owner_id, expected_head=head_before)

    app_facts = build_app_facts(
        owner_id,
        service.list_entries(owner_id),
        ("Maria",),
        death_triggered=True,
        policy_frozen=True,
    )
    policy = parse(
        'release letter "To Maria" to maria when date >= 2040-05-01\n'
    )
    bridge = PrologAccessBridge(swipl_executable, timeout_seconds=5.0)
    request_one = AccessRequest(
        "maria", "letter-one", "verbatim", date(2040, 5, 1)
    )
    assert bridge.can_access_many(policy, app_facts, (request_one,)) == (
        "allow",
    )

    duplicate_facts = replace(
        app_facts,
        entries=app_facts.entries + (EntryFact("letter-two", "letter"),),
        letters=app_facts.letters + (("letter-two", "To Maria"),),
    )
    decisions = bridge.can_access_many(
        policy,
        duplicate_facts,
        (
            request_one,
            AccessRequest(
                "maria", "letter-two", "verbatim", date(2040, 5, 1)
            ),
        ),
    )

    assert decisions == ("deny", "deny")


def test_ambiguous_names_leave_repository_and_chain_unchanged():
    repository = InMemoryEntryRepository()
    service = DiaryService(repository)
    timestamp = datetime(2026, 11, 14, 10, tzinfo=timezone.utc)
    service.add_diary_entry("owner-lola", "existing", "A first note.", timestamp)
    records_before = service.list_entries("owner-lola")
    head_before = service.head_hash("owner-lola")
    people = (
        PersonReference("alex-1", "Alex Smith", ("Alex",)),
        PersonReference("alex-2", "Alex Jones", ("Alex",)),
    )

    with pytest.raises(AmbiguousName) as error:
        service.add_diary_entry(
            "owner-lola",
            "ambiguous",
            "Alex visited.",
            datetime(2026, 11, 14, 11, tzinfo=timezone.utc),
            people,
        )

    assert error.value.detail == {
        "name": "Alex",
        "candidates": ("Alex Smith", "Alex Jones"),
    }
    assert service.list_entries("owner-lola") == records_before
    assert service.head_hash("owner-lola") == head_before


def test_naive_datetimes_are_rejected_and_hash_timestamp_matches_entry():
    repository = InMemoryEntryRepository()
    service = DiaryService(repository)

    with pytest.raises(ValueError, match="timezone-aware"):
        service.add_diary_entry(
            "owner-lola", "naive", "No local-time ambiguity.", datetime(2026, 11, 14)
        )
    assert service.list_entries("owner-lola") == ()
    assert service.head_hash("owner-lola") is None

    timestamp = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)
    record = service.add_diary_entry(
        "owner-lola", "aware", "An aware timestamp.", timestamp
    )
    assert record.entry.created_at == timestamp
    assert record.chain_entry.entry.timestamp == timestamp


def test_two_owners_have_independent_chains_and_scoped_heads():
    repository = InMemoryEntryRepository()
    service = DiaryService(repository)
    timestamp = datetime(2026, 11, 14, 13, tzinfo=timezone.utc)

    first = service.add_diary_entry("owner-one", "same-id", "Same text.", timestamp)
    second = service.add_diary_entry("owner-two", "same-id", "Same text.", timestamp)

    assert first.chain_entry.previous_hash == ""
    assert second.chain_entry.previous_hash == ""
    assert first.chain_entry.digest != second.chain_entry.digest
    assert service.head_hash("owner-one") == first.chain_entry.digest
    assert service.head_hash("owner-two") == second.chain_entry.digest
    assert service.verify("owner-one", expected_head=first.chain_entry.digest)
    assert service.verify("owner-two", expected_head=second.chain_entry.digest)


def test_verify_checks_expected_head_and_detects_chain_tampering(
    maria_store_sample: MariaStoreSample,
):
    sample = maria_store_sample
    actual_head = sample.service.head_hash(sample.owner_id)

    assert actual_head is not None
    assert sample.service.verify(sample.owner_id, expected_head=actual_head)
    with pytest.raises(TamperDetected):
        sample.service.verify(sample.owner_id, expected_head="stale-head")

    tampered = replace(
        sample.records[-1],
        chain_entry=replace(sample.records[-1].chain_entry, digest="0" * 64),
    )
    sample.repository._entries[sample.owner_id][-1] = tampered
    with pytest.raises(TamperDetected):
        sample.service.verify(sample.owner_id)


def test_reads_do_not_automatically_verify_the_chain(
    maria_store_sample: MariaStoreSample, monkeypatch: pytest.MonkeyPatch
):
    sample = maria_store_sample

    def unexpected_verification(*args, **kwargs):
        pytest.fail("read methods must not verify before an access check")

    monkeypatch.setattr(sample.service, "verify", unexpected_verification)

    assert sample.service.get_entry(sample.owner_id, "e_maria") is not None
    assert len(sample.service.list_entries(sample.owner_id)) == 5


def test_build_app_facts_casefolds_names_and_tags_and_rejects_other_owners(
    maria_store_sample: MariaStoreSample,
):
    sample = maria_store_sample

    assert sample.app_facts.registered_people == ("maria", "nora")
    assert ("e_family", "maria") in sample.app_facts.entry_mentions
    assert ("e_family", "family") in sample.app_facts.entry_tags
    assert ("e_business", "business") in sample.app_facts.entry_tags
    assert sample.app_facts.death_triggered is True
    assert sample.app_facts.policy_frozen is True
    with pytest.raises(ValueError, match="belong to the requested owner"):
        build_app_facts(
            "different-owner",
            sample.records,
            ("Maria", "Nora"),
            death_triggered=True,
            policy_frozen=True,
        )


def test_maria_handout_rows_run_through_the_required_prolog_bridge(
    maria_store_sample: MariaStoreSample,
    swipl_executable: str,
):
    rows = _maria_acceptance_rows()
    assert len(rows) == 6
    requests = tuple(
        AccessRequest(
            person=row["Asker"],
            entry_id=row["Entry ID"],
            level=row["Level"],
            today=date.fromisoformat(row["Today"]),
        )
        for row in rows
    )
    policy = parse(MARIA_POLICY_PATH.read_text(encoding="utf-8"))
    bridge = PrologAccessBridge(swipl_executable, timeout_seconds=5.0)

    decisions = bridge.can_access_many(
        policy, maria_store_sample.app_facts, requests
    )

    assert decisions == tuple(row["Expected"] for row in rows)
    assert decisions == ("allow", "allow", "deny", "allow", "deny", "deny")


def test_diary_domain_and_services_do_not_import_flask_or_database_packages():
    app_dir = Path(__file__).parents[1] / "app"
    source_paths = tuple(
        (app_dir / "domain" / "diary").rglob("*.py")
    ) + tuple((app_dir / "services").rglob("*.py"))
    prohibited_roots = {"flask", "sqlalchemy", "pymysql"}

    for source_path in source_paths:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                assert prohibited_roots.isdisjoint(roots)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".", 1)[0] not in prohibited_roots
