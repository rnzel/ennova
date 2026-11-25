# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Object-oriented diary model tests
import ast
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.domain.diary import (
    AccessLevel,
    Beneficiary,
    DiaryEntry,
    Entry,
    Grant,
    LetterEntry,
    Owner,
    Protocol,
    Vault,
)


def test_entry_hierarchy_and_polymorphic_kind():
    created_at = datetime(2026, 11, 12, tzinfo=timezone.utc)
    diary = DiaryEntry("diary-1", created_at, "A diary entry.")
    letter = LetterEntry(
        "letter-1",
        created_at,
        "A letter.",
        "A note",
        "Maria",
        date(2040, 5, 1),
    )

    assert isinstance(diary, Entry)
    assert isinstance(letter, Entry)
    assert diary.kind == "diary"
    assert letter.kind == "letter"
    assert letter.title == "A note"
    assert letter.recipient == "Maria"
    assert letter.release_date == date(2040, 5, 1)
    with pytest.raises(TypeError):
        Entry("entry-1", created_at, "Cannot instantiate an abstract entry.")


def test_entry_content_and_metadata_are_read_only():
    entry = DiaryEntry("diary-1", datetime(2026, 11, 12), "Original text.")

    with pytest.raises(AttributeError):
        entry.original_content = "Changed text."
    with pytest.raises(AttributeError):
        entry.entry_id = "changed-id"


def test_vault_appends_retrieves_and_returns_immutable_snapshots():
    vault = Vault()
    first = DiaryEntry("diary-1", datetime(2026, 11, 12), "First.")
    second = LetterEntry(
        "letter-1", datetime(2026, 11, 13), "Second.", "Title", "Maria"
    )

    vault.append(first)
    initial_snapshot = vault.entries
    vault.append(second)

    assert vault.get("diary-1") is first
    assert vault.get("missing") is None
    assert vault.entries == (first, second)
    assert initial_snapshot == (first,)
    with pytest.raises(AttributeError):
        vault.entries.append(first)
    with pytest.raises(AttributeError):
        vault._entries

    # A caller cannot mutate the vault by retaining or changing an exposed snapshot.
    assert isinstance(vault.entries, tuple)
    assert vault.entries == (first, second)


def test_vault_rejects_duplicate_ids_and_has_no_edit_or_delete_methods():
    vault = Vault()
    vault.append(DiaryEntry("diary-1", datetime(2026, 11, 12), "First."))

    with pytest.raises(ValueError, match="Entry ID already exists"):
        vault.append(DiaryEntry("diary-1", datetime(2026, 11, 13), "Duplicate."))
    assert not hasattr(vault, "update")
    assert not hasattr(vault, "delete")
    assert not hasattr(vault, "remove")


def test_owner_beneficiary_and_protocol_keep_encapsulated_identity_and_grants():
    owner = Owner("owner-1", "Lola Reyes")
    beneficiary_protocol = Protocol()
    beneficiary = Beneficiary("beneficiary-1", "Maria", beneficiary_protocol)
    grant = Grant(
        beneficiary.beneficiary_id,
        'entries tagged "family"',
        AccessLevel.SUMMARY,
    )
    owner.protocol.add_grant(grant)

    assert owner.name == "Lola Reyes"
    assert isinstance(owner.vault, Vault)
    assert isinstance(owner.protocol, Protocol)
    assert beneficiary.name == "Maria"
    assert beneficiary.protocol is beneficiary_protocol
    assert owner.protocol.grants == (grant,)
    with pytest.raises(AttributeError):
        owner.name = "Changed"
    with pytest.raises(AttributeError):
        owner.protocol.grants.append(grant)
    with pytest.raises(AttributeError):
        beneficiary.protocol = Protocol()


def test_beneficiary_protocol_is_optional_and_type_checked():
    beneficiary = Beneficiary("beneficiary-1", "Maria")

    assert beneficiary.protocol is None
    with pytest.raises(TypeError, match="Protocol or None"):
        Beneficiary("beneficiary-2", "Adam", object())


def test_diary_domain_modules_do_not_import_flask_or_database_packages():
    domain_dir = Path(__file__).parents[1] / "app" / "domain"
    prohibited_roots = {"flask", "sqlalchemy", "pymysql"}

    for source_path in domain_dir.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
                assert prohibited_roots.isdisjoint(imported_roots)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".", 1)[0] not in prohibited_roots
