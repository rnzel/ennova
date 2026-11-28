# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Functional entry processing tests
import ast
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.domain.processing import (
    AmbiguousName,
    ChainedEntry,
    CorrectionRule,
    DiffSegment,
    EntryData,
    PersonReference,
    TamperDetected,
    correct,
    diff,
    extract_names,
    extract_topics,
    hash_chain,
    hash_entry,
    normalize,
    verify_hash_chain,
)


def test_normalize_canonicalizes_unicode_and_newlines_only():
    source = "Cafe\u0301\r\nSecond line\rThird line  "

    result = normalize(source)

    assert result == "Café\nSecond line\nThird line  "
    assert source == "Cafe\u0301\r\nSecond line\rThird line  "


def test_normalize_returns_empty_text_for_empty_input():
    assert normalize("") == ""


def test_extract_names_reads_links_and_known_aliases_in_order():
    people = (
        PersonReference("p1", "Maria Santos", ("Maria",)),
        PersonReference("p2", "Lola Reyes", ("Lola",)),
    )

    result = extract_names(
        "I wrote to [[Maria Santos]], then spoke with Lola and [[Maria]].", people
    )

    assert result == ("Maria Santos", "Lola Reyes")


def test_extract_names_returns_empty_result_for_empty_text():
    assert extract_names("") == ()


def test_extract_names_deduplicates_repeated_identical_references():
    assert extract_names("I met [[Alex]] and later saw [[Alex]].") == ("Alex",)


def test_extract_names_returns_unresolved_links_and_raises_for_ambiguous_alias():
    assert extract_names("A note for [[Unknown Person]].") == ("Unknown Person",)
    people = (
        PersonReference("p1", "Alex Smith", ("Alex",)),
        PersonReference("p2", "Alex Jones", ("Alex",)),
    )

    with pytest.raises(AmbiguousName):
        extract_names("Alex called.", people)


def test_extract_topics_casefolds_and_deduplicates_in_first_seen_order():
    assert extract_topics("Today #Family, tomorrow #work; again #family.") == (
        "family",
        "work",
    )


def test_extract_topics_returns_empty_result_for_empty_text():
    assert extract_topics("") == ()


def test_correct_applies_immutable_rules_in_order_and_preserves_simple_case():
    rules = (
        CorrectionRule("teh", "the"),
        CorrectionRule("alot", "a lot"),
    )
    source = "Teh note says alot, but the other word is untouched."

    result = correct(source, rules)

    assert result == "The note says a lot, but the other word is untouched."
    assert source == "Teh note says alot, but the other word is untouched."
    with pytest.raises(FrozenInstanceError):
        rules[0].source = "changed"


def test_correct_returns_empty_text_for_empty_input_with_rules():
    rules = (CorrectionRule("teh", "the"),)

    assert correct("", rules) == ""


def test_diff_segments_reconstruct_both_original_and_updated_text():
    before = "I liked teh story."
    after = "I liked the story!"
    segments = diff(before, after)

    reconstructed_before = "".join(
        segment.text for segment in segments if segment.operation in ("equal", "delete")
    )
    reconstructed_after = "".join(
        segment.text for segment in segments if segment.operation in ("equal", "insert")
    )

    assert reconstructed_before == before
    assert reconstructed_after == after
    assert any(segment.operation == "delete" for segment in segments)
    assert any(segment.operation == "insert" for segment in segments)


def test_diff_returns_no_segments_for_two_empty_texts():
    assert diff("", "") == ()


def test_diff_represents_empty_to_text_as_insertion():
    assert diff("", "new text") == (DiffSegment("insert", "new text"),)


def test_diff_represents_text_to_empty_as_deletion():
    assert diff("old text", "") == (DiffSegment("delete", "old text"),)


def test_entry_data_is_frozen_and_metadata_is_immutable():
    entry = EntryData(
        "Original.",
        datetime(2026, 11, 12, tzinfo=timezone.utc),
        (("kind", "diary"),),
    )

    with pytest.raises(FrozenInstanceError):
        entry.original_content = "Changed."
    with pytest.raises(TypeError):
        EntryData("Original.", datetime(2026, 11, 12), [("kind", "diary")])


def test_hash_chain_is_deterministic_and_links_each_entry_to_its_predecessor():
    entries = (
        EntryData(
            "First original.",
            datetime(2026, 11, 12, tzinfo=timezone.utc),
            (("kind", "diary"), ("topic", "family")),
        ),
        EntryData(
            "Second original.",
            datetime(2026, 11, 13, tzinfo=timezone.utc),
            (("kind", "letter"),),
        ),
    )

    chain = hash_chain(entries)
    same_chain = hash_chain(entries)

    assert chain == same_chain
    assert chain[0].previous_hash == ""
    assert chain[1].previous_hash == chain[0].digest
    assert verify_hash_chain(chain) is True
    assert hash_entry(entries[0], "").digest == chain[0].digest


@pytest.mark.parametrize(
    "tampered_entry",
    [
        EntryData(
            "Changed content.",
            datetime(2026, 11, 12, tzinfo=timezone.utc),
            (("kind", "diary"),),
        ),
        EntryData(
            "Original.",
            datetime(2026, 11, 13, tzinfo=timezone.utc),
            (("kind", "diary"),),
        ),
        EntryData(
            "Original.",
            datetime(2026, 11, 12, tzinfo=timezone.utc),
            (("kind", "letter"),),
        ),
    ],
)
def test_hash_chain_detects_content_timestamp_and_metadata_tampering(tampered_entry):
    original = EntryData(
        "Original.",
        datetime(2026, 11, 12, tzinfo=timezone.utc),
        (("kind", "diary"),),
    )
    chain = hash_chain((original,))
    tampered = (replace(chain[0], entry=tampered_entry),)

    with pytest.raises(TamperDetected):
        verify_hash_chain(tampered)


def test_hash_chain_detects_digest_and_predecessor_link_tampering():
    first = EntryData("First.", datetime(2026, 11, 12, tzinfo=timezone.utc))
    second = EntryData("Second.", datetime(2026, 11, 13, tzinfo=timezone.utc))
    chain = hash_chain((first, second))

    bad_digest = (replace(chain[0], digest="0" * 64), chain[1])
    bad_link = (chain[0], replace(chain[1], previous_hash="0" * 64))

    with pytest.raises(TamperDetected):
        verify_hash_chain(bad_digest)
    with pytest.raises(TamperDetected):
        verify_hash_chain(bad_link)


def test_hash_chain_detects_changed_entry_content():
    entry = EntryData("Original.", datetime(2026, 11, 12, tzinfo=timezone.utc))
    chain = hash_chain((entry,))
    changed = replace(
        chain[0], entry=replace(chain[0].entry, original_content="Changed.")
    )

    with pytest.raises(TamperDetected) as error:
        verify_hash_chain((changed,))

    assert error.value.detail == {"reason": "entry hash mismatch", "position": 0}
    assert "position 0" in str(error.value)
    assert "entry hash mismatch" in str(error.value)


def test_hash_chain_detects_removed_interior_entry():
    entries = tuple(
        EntryData(text, datetime(2026, 11, day, tzinfo=timezone.utc))
        for day, text in ((12, "First."), (13, "Removed."), (14, "Last."))
    )
    chain = hash_chain(entries)

    with pytest.raises(TamperDetected) as error:
        verify_hash_chain((chain[0], chain[2]))

    assert error.value.detail == {
        "reason": "hash-chain link mismatch",
        "position": 1,
    }


def test_hash_chain_detects_reordered_entries():
    entries = (
        EntryData("First.", datetime(2026, 11, 12, tzinfo=timezone.utc)),
        EntryData("Second.", datetime(2026, 11, 13, tzinfo=timezone.utc)),
    )
    chain = hash_chain(entries)

    with pytest.raises(TamperDetected) as error:
        verify_hash_chain(tuple(reversed(chain)))

    assert error.value.detail == {
        "reason": "hash-chain link mismatch",
        "position": 0,
    }


def test_hash_chain_reports_only_the_first_broken_link():
    entries = tuple(
        EntryData(text, datetime(2026, 11, day, tzinfo=timezone.utc))
        for day, text in ((12, "First."), (13, "Second."), (14, "Third."))
    )
    chain = hash_chain(entries)
    tampered = (
        chain[0],
        replace(chain[1], previous_hash="bad-link"),
        replace(chain[2], previous_hash="another-bad-link"),
    )

    with pytest.raises(TamperDetected) as error:
        verify_hash_chain(tampered)

    assert error.value.detail == {
        "reason": "hash-chain link mismatch",
        "position": 1,
    }


def test_hash_chain_detects_modified_previous_hash():
    entries = (
        EntryData("First.", datetime(2026, 11, 12, tzinfo=timezone.utc)),
        EntryData("Second.", datetime(2026, 11, 13, tzinfo=timezone.utc)),
    )
    chain = hash_chain(entries)
    tampered = (chain[0], replace(chain[1], previous_hash="wrong-previous-hash"))

    with pytest.raises(TamperDetected) as error:
        verify_hash_chain(tampered)

    assert error.value.detail == {
        "reason": "hash-chain link mismatch",
        "position": 1,
    }


def test_processing_modules_have_no_io_clock_random_flask_or_database_dependencies():
    processing_dir = Path(__file__).parents[1] / "app" / "domain" / "processing"
    prohibited_imports = {
        "flask",
        "sqlalchemy",
        "pymysql",
        "os",
        "pathlib",
        "io",
        "socket",
        "subprocess",
        "random",
        "secrets",
        "time",
    }
    prohibited_calls = {"open", "now", "today", "urandom", "randint", "random"}

    for source_path in processing_dir.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
                assert prohibited_imports.isdisjoint(imported_roots)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".", 1)[0] not in prohibited_imports
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in prohibited_calls
                elif isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in prohibited_calls
