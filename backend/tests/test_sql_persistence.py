from datetime import date, datetime, timezone
import importlib.util
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

from app import create_app
from app.extensions import db
from app.infrastructure.sql_persistence import (
    SQLAlchemyApiState, SQLAlchemyEntryRepository, SQLAlchemyOwnerConversationStore,
    SQLAlchemySummaryStore,
)
from app.models import AccountRecord
from app.ai.model_summaries import SummaryArtifact
from app.policy import parse
from app.services.api_state import AuditRecord
from app.services.diary_service import DiaryService
from app.domain.processing import PersonReference, verify_hash_chain
from app.models.application_persistence import (
    DiaryEntryNameRecord,
    DiaryEntryRecord,
    DiaryEntryTopicRecord,
)


@pytest.fixture
def sql_app(tmp_path):
    app = create_app(config_overrides={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'ennova.sqlite'}",
        "JWT_SECRET_KEY": "test-secret",
    })
    with app.app_context():
        db.create_all()
        db.session.add(AccountRecord(account_id="owner-a", username="owner", email="owner@example.test",
            owner_id="owner-a", person_id="owner", role="owner", password_hash="test-hash"))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


def test_diary_rows_reconstruct_hash_and_isolate_owner(sql_app):
    with sql_app.app_context():
        repo = SQLAlchemyEntryRepository()
        service = DiaryService(repo)
        timestamp = datetime(2025, 3, 1, 12, 30, tzinfo=timezone.utc)
        created = service.add_diary_entry("owner-a", "entry-1", "A note #travel", timestamp)
        loaded = repo.get("owner-a", "entry-1")
        assert loaded.entry.created_at.isoformat() == timestamp.isoformat()
        assert loaded.topics == ("travel",)
        assert repo.get("other-owner", "entry-1") is None
        assert verify_hash_chain(tuple(x.chain_entry for x in repo.list_for_owner("owner-a")))
        assert created.chain_entry.digest == repo.head_hash("owner-a")


def test_letter_release_date_tags_and_hash_round_trip(sql_app):
    with sql_app.app_context():
        repo = SQLAlchemyEntryRepository()
        service = DiaryService(repo)
        release = date(2040, 5, 1)
        service.add_letter_entry(
            "owner-a", "letter-1", "A letter #family", "To Maria", "Maria",
            datetime(2025, 3, 1, 12, 30, tzinfo=timezone.utc),
            release_date=release,
        )
        loaded = repo.get("owner-a", "letter-1")
        assert loaded.entry.release_date == release
        assert loaded.entry.tags == ("family",)
        assert verify_hash_chain(tuple(x.chain_entry for x in repo.list_for_owner("owner-a")))


def test_sqlalchemy_rejects_diary_entry_update_and_delete(sql_app):
    with sql_app.app_context():
        service = DiaryService(SQLAlchemyEntryRepository())
        service.add_diary_entry(
            "owner-a",
            "entry-immutable",
            "A note about Alex #family.",
            datetime(2026, 11, 14, 10, tzinfo=timezone.utc),
            (PersonReference("alex", "Alex Smith", ("Alex",)),),
        )
        record = db.session.get(DiaryEntryRecord, ("owner-a", "entry-immutable"))
        record.content = "Edited content."
        with pytest.raises(ValueError, match="append-only"):
            db.session.flush()
        db.session.rollback()

        record = db.session.get(DiaryEntryRecord, ("owner-a", "entry-immutable"))
        db.session.delete(record)
        with pytest.raises(ValueError, match="append-only"):
            db.session.flush()
        db.session.rollback()


@pytest.mark.parametrize(
    ("evidence_model", "field_name", "operation"),
    (
        (DiaryEntryNameRecord, "name", "update"),
        (DiaryEntryNameRecord, "name", "delete"),
        (DiaryEntryTopicRecord, "topic", "update"),
        (DiaryEntryTopicRecord, "topic", "delete"),
    ),
)
def test_sqlalchemy_rejects_related_entry_evidence_update_and_delete(
    sql_app, evidence_model, field_name, operation
):
    with sql_app.app_context():
        service = DiaryService(SQLAlchemyEntryRepository())
        service.add_diary_entry(
            "owner-a",
            "entry-evidence",
            "Alex wrote about #family.",
            datetime(2026, 11, 14, 10, tzinfo=timezone.utc),
            (PersonReference("alex", "Alex Smith", ("Alex",)),),
        )
        evidence = db.session.get(
            evidence_model, ("owner-a", "entry-evidence", 0)
        )
        if operation == "update":
            setattr(evidence, field_name, "Changed evidence")
        else:
            db.session.delete(evidence)
        with pytest.raises(ValueError, match="append-only"):
            db.session.flush()
        db.session.rollback()


def test_access_state_summaries_and_owner_context_are_durable(sql_app):
    with sql_app.app_context():
        state = SQLAlchemyApiState()
        DiaryService(SQLAlchemyEntryRepository()).add_diary_entry(
            "owner-a", "entry-x", "Some recorded text.", datetime.now(timezone.utc)
        )
        state.accept_policy("owner-a", "protocol maria:\n", parse("protocol maria:\n"), datetime.now(timezone.utc))
        state.add_audit(AuditRecord("owner-a", "owner-a", "policy_update", "accepted", datetime.now(timezone.utc)))
        state.trigger("owner-a")
        SQLAlchemySummaryStore().put(SummaryArtifact("owner-a", "entry-x", "derived", "digest"))
        conversations = SQLAlchemyOwnerConversationStore()
        conversation_id, _ = conversations.start_or_load("owner-a", None)
        conversations.record_question("owner-a", conversation_id, "first question")
        db.session.remove()

        state = SQLAlchemyApiState()
        assert state.active_policy("owner-a").version == 1
        assert state.is_triggered("owner-a")
        assert len(state.audits()) == 1
        assert SQLAlchemySummaryStore().get("owner-a", "entry-x").text == "derived"
        assert conversations.start_or_load("owner-a", conversation_id)[1] == ("first question",)
        with pytest.raises(ValueError, match="unavailable"):
            conversations.start_or_load("other-owner", conversation_id)


def test_forward_migrations_apply_to_disposable_sqlite():
    backend = Path(__file__).parents[1]
    revisions = sorted((backend / "migrations" / "versions").glob("*.py"))
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            for index, path in enumerate(revisions):
                spec = importlib.util.spec_from_file_location(f"migration_{index}", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.upgrade()
        tables = set(inspect(connection).get_table_names())
    assert {"accounts", "invitations", "diary_entries", "policy_versions",
            "owner_conversations", "audit_events"}.issubset(tables)
