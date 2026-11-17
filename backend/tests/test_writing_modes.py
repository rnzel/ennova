# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Object-oriented writing-mode tests and F7 boundary tests
from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.ai.client import FakeModelClient, ModelResponse, ToolCall
from app.ai.summaries import InMemorySummaryStore
from app.domain.diary import InMemoryEntryRepository, StoredEntry
from app.domain.processing import CorrectionRule
from app.domain.writing_modes import (
    LONG_SENTENCE_WORD_THRESHOLD,
    DerivedVersion,
    InMemoryDerivedVersionStore,
    LightFix,
    Review,
    ReviewSuggestion,
    Verbatim,
    WritingMode,
    get_writing_mode,
    resolve_writing_mode,
)
from app.errors import UnknownWritingMode
from app.policy import (
    DefaultWritingMode,
    Policy,
    PrologAccessBridge,
    parse,
)
from app.services.access_facts import build_app_facts
from app.services.diary_service import DiaryService
from app.services.grounded_qa import GroundedQAService

ROOT = Path(__file__).parents[2]


@pytest.fixture
def stored_entry() -> StoredEntry:
    service = DiaryService(InMemoryEntryRepository())
    return service.add_diary_entry(
        "owner-lola",
        "entry-1",
        "Teh note says alot #note",
        datetime(2026, 11, 17, tzinfo=timezone.utc),
    )


def test_writing_mode_is_abstract():
    with pytest.raises(TypeError):
        WritingMode()


def test_verbatim_preserves_original_and_has_no_diff(stored_entry: StoredEntry):
    original = stored_entry.entry.original_content
    digest = stored_entry.chain_entry.digest

    version = Verbatim().process(stored_entry)

    assert version == DerivedVersion(
        "entry-1", digest, "verbatim", original, ()
    )
    assert stored_entry.entry.original_content == original
    assert stored_entry.chain_entry.digest == digest


def test_light_fix_reuses_f2_rules_without_changing_source(stored_entry: StoredEntry):
    version = LightFix(
        (CorrectionRule("teh", "the"), CorrectionRule("alot", "a lot"))
    ).process(stored_entry)

    assert version.text == "The note says a lot #note"
    assert version.changes
    assert stored_entry.entry.original_content == "Teh note says alot #note"


def test_light_fix_letter_preserves_digest_and_letter_behavior():
    service = DiaryService(InMemoryEntryRepository())
    letter = service.add_letter_entry(
        "owner-lola",
        "letter-1",
        "Teh letter says alot",
        "To Maria",
        "Maria",
        datetime(2026, 11, 17, tzinfo=timezone.utc),
    )
    original = letter.entry.original_content
    digest = letter.chain_entry.digest

    version = LightFix((CorrectionRule("teh", "the"),)).process(letter)

    assert version.text == "The letter says alot"
    assert letter.entry.original_content == original
    assert letter.chain_entry.digest == digest
    assert service.get_entry("owner-lola", "letter-1") == letter


def test_review_reports_exact_suggestion_records():
    long_sentence = " ".join(f"word{i}" for i in range(LONG_SENTENCE_WORD_THRESHOLD + 1))
    source = f"{long_sentence} This this ends"
    service = DiaryService(InMemoryEntryRepository())
    entry = service.add_diary_entry(
        "owner-lola",
        "review-1",
        source,
        datetime(2026, 11, 17, tzinfo=timezone.utc),
    )

    version = Review().process(entry)

    assert version.text == source
    assert tuple(item.code for item in version.suggestions) == (
        "long_sentence",
        "repeated_word",
        "missing_terminal_punctuation",
    )
    assert all(isinstance(item, ReviewSuggestion) for item in version.suggestions)
    assert all(item.message for item in version.suggestions)
    assert version.suggestions[-1].position == len(source)


def test_review_optional_rewrite_and_no_matching_rule_is_unchanged(stored_entry):
    unchanged = Review((CorrectionRule("missing", "present"),), rewrite=True).process(
        stored_entry
    )
    rewritten = Review((CorrectionRule("teh", "the"),), rewrite=True).process(
        stored_entry
    )

    assert unchanged.text == stored_entry.entry.original_content
    assert rewritten.text == "The note says alot #note"


def test_derived_version_is_frozen_and_collections_are_tuples():
    version = DerivedVersion("entry", "digest", "review", "text", ())

    with pytest.raises(FrozenInstanceError):
        version.text = "changed"
    with pytest.raises(TypeError):
        DerivedVersion("entry", "digest", "review", "text", [])


def test_registry_dispatches_without_mode_conditionals():
    assert isinstance(get_writing_mode("verbatim"), Verbatim)
    assert isinstance(get_writing_mode("light_fix"), LightFix)
    assert isinstance(get_writing_mode("review"), Review)


def test_unknown_mode_error_and_safe_resolver_fallback():
    with pytest.raises(UnknownWritingMode):
        get_writing_mode("unknown")

    mode, fell_back = resolve_writing_mode(
        Policy((DefaultWritingMode("unknown"),))
    )

    assert isinstance(mode, Verbatim)
    assert fell_back is True


def test_policy_without_default_resolves_verbatim_without_raising():
    mode, fell_back = resolve_writing_mode(parse("trustee is adam\n"))

    assert isinstance(mode, Verbatim)
    assert fell_back is True


def test_last_default_writing_mode_wins():
    policy = Policy(
        (DefaultWritingMode("review"), DefaultWritingMode("light_fix"))
    )

    mode, fell_back = resolve_writing_mode(policy)

    assert isinstance(mode, LightFix)
    assert fell_back is False


def test_process_requires_stored_entry():
    with pytest.raises(TypeError, match="StoredEntry"):
        Verbatim().process("original")  # type: ignore[arg-type]


def test_derived_store_is_append_only_and_reports_staleness(stored_entry):
    version = Verbatim().process(stored_entry)
    store = InMemoryDerivedVersionStore()

    stored = store.append(version, 1)

    assert stored.version == version
    assert store.list_all() == (stored,)
    assert store.matches_current(version, stored_entry)
    with pytest.raises(ValueError):
        store.append(version, 1)
    with pytest.raises(AttributeError):
        store.update(version)
    with pytest.raises(AttributeError):
        store.delete(version)

    changed = replace(
        stored_entry,
        chain_entry=replace(stored_entry.chain_entry, digest="changed"),
    )
    assert not store.matches_current(version, changed)


def test_writing_modes_have_no_infrastructure_or_ai_imports():
    writing_modes = ROOT / "backend" / "app" / "domain" / "writing_modes"
    prohibited = {
        "flask",
        "sqlalchemy",
        "pymysql",
        "app.ai",
        "subprocess",
        "time",
        "datetime",
        "random",
    }
    for path in writing_modes.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            module = (
                node.module
                if isinstance(node, ast.ImportFrom)
                else node.names[0].name
                if isinstance(node, ast.Import) and node.names
                else None
            )
            if module:
                assert not any(
                    module == item or module.startswith(item + ".")
                    for item in prohibited
                )


def test_f7_does_not_import_derived_versions():
    paths = list((ROOT / "backend" / "app" / "ai").rglob("*.py"))
    paths.append(ROOT / "backend" / "app" / "services" / "grounded_qa.py")
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert "DerivedVersion" not in {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }


def test_derived_canary_never_reaches_grounded_prompts_or_tool_results(
    stored_entry: StoredEntry,
    swipl_executable: str,
):
    canary = "DERIVED-CANARY-7f3a"
    derived = replace(
        Verbatim().process(stored_entry),
        text=canary,
    )
    assert derived.text == canary

    model = FakeModelClient(
        (
            ModelResponse(
                "",
                tool_calls=(ToolCall("search_entries", {"query": "note"}),),
            ),
            ModelResponse("A permitted answer.", citation_ids=("entry-1",)),
        )
    )
    facts = build_app_facts(
        "owner-lola",
        (stored_entry,),
        ("Maria",),
        death_triggered=True,
        policy_frozen=True,
    )
    repository = InMemoryEntryRepository()
    repository.append(stored_entry)
    response = GroundedQAService(
        DiaryService(repository),
        PrologAccessBridge(swipl_executable),
        model,
        InMemorySummaryStore(),
    )
    result = response.answer(
        "What is in the note?",
        owner_id="owner-lola",
        asker="maria",
        policy_source='protocol maria:\n    may read verbatim of entries tagged "note"\n',
        app_facts=facts,
        today=datetime(2026, 11, 17, tzinfo=timezone.utc).date(),
    )
    assert result.text == "A permitted answer."
    recorded = "\n".join(
        prompt.system_prompt
        + "\n"
        + "\n".join(message.content for message in prompt.messages)
        for prompt in model.prompts
    )
    assert canary not in recorded
