from datetime import datetime, timezone
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
from app.domain.processing import verify_hash_chain


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
