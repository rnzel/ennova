"""SQLAlchemy repositories for durable diary, access state and AI context."""
from datetime import datetime, timezone

from sqlalchemy import select, func

from app.extensions import db
from app.models.account_persistence import AccountRecord
from app.models.application_persistence import (
    AuditEventRecord, DiaryEntryNameRecord, DiaryEntryRecord, DiaryEntryTopicRecord, DerivedSummaryRecord,
    OwnerConversationRecord, OwnerLifecycleRecord, OwnerQuestionRecord,
    PolicyVersionRecord,
)
from app.domain.diary import DiaryEntry, EntryRepository, LetterEntry, StoredEntry
from app.domain.processing import ChainedEntry, EntryData
from app.services.api_state import AuditRecord, PolicyVersion
from app.policy import parse
from app.ai.model_summaries import SummaryArtifact


def _aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _stored(row):
    timestamp = datetime.fromisoformat(row.source_timestamp)
    metadata = [("entry_id", row.entry_id), ("owner_id", row.owner_id), ("kind", row.kind)]
    metadata.extend(("name", item.name) for item in row.names)
    metadata.extend(("topic", item.topic) for item in row.topics)
    if row.kind == "letter":
        metadata.extend((("title", row.title), ("recipient", row.recipient)))
    data = EntryData(row.content, timestamp, tuple(metadata))
    entry = (LetterEntry(row.entry_id, timestamp, row.content, row.title, row.recipient)
             if row.kind == "letter" else DiaryEntry(row.entry_id, timestamp, row.content))
    return StoredEntry(row.owner_id, entry, tuple(x.name for x in row.names),
                       tuple(x.topic for x in row.topics),
                       ChainedEntry(data, row.previous_hash, row.digest))


class SQLAlchemyEntryRepository(EntryRepository):
    """Owner scoped append-only repository. Database rows retain exact hash inputs."""
    def append(self, record):
        if not isinstance(record, StoredEntry):
            raise TypeError("record must be a StoredEntry.")
        try:
            # Serialize chain appends for one owner. The unique sequence constraint is
            # the final guard if a dialect cannot provide row-level locking.
            db.session.execute(select(AccountRecord.account_id).where(
                AccountRecord.account_id == record.owner_id).with_for_update()).scalar_one()
            last = db.session.execute(select(DiaryEntryRecord).where(
                DiaryEntryRecord.owner_id == record.owner_id).order_by(
                    DiaryEntryRecord.sequence.desc()).limit(1)).scalar_one_or_none()
            expected = last.digest if last else ""
            if expected != record.chain_entry.previous_hash:
                raise ValueError("The hash record does not extend this owner's chain.")
            if db.session.get(DiaryEntryRecord, (record.owner_id, record.entry.entry_id)):
                raise ValueError(f"Entry ID already exists: {record.entry.entry_id}")
            row = DiaryEntryRecord(
                owner_id=record.owner_id, entry_id=record.entry.entry_id,
                sequence=(last.sequence + 1 if last else 1), kind=record.entry.kind,
                content=record.entry.original_content,
                source_timestamp=record.entry.created_at.isoformat(),
                created_at=record.entry.created_at, title=getattr(record.entry, "title", None),
                recipient=getattr(record.entry, "recipient", None),
                previous_hash=record.chain_entry.previous_hash, digest=record.chain_entry.digest)
            row.names = [DiaryEntryNameRecord(ordinal=i, name=x) for i, x in enumerate(record.names)]
            row.topics = [DiaryEntryTopicRecord(ordinal=i, topic=x) for i, x in enumerate(record.topics)]
            db.session.add(row)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def get(self, owner_id, entry_id):
        row = db.session.get(DiaryEntryRecord, (owner_id, entry_id))
        return _stored(row) if row else None

    def list_for_owner(self, owner_id):
        rows = db.session.execute(select(DiaryEntryRecord).where(
            DiaryEntryRecord.owner_id == owner_id).order_by(DiaryEntryRecord.sequence)).scalars()
        return tuple(_stored(row) for row in rows)

    def head_hash(self, owner_id):
        return db.session.execute(select(DiaryEntryRecord.digest).where(
            DiaryEntryRecord.owner_id == owner_id).order_by(
                DiaryEntryRecord.sequence.desc()).limit(1)).scalar_one_or_none()


class SQLAlchemyApiState:
    """Durable accepted policy versions, one-way lifecycle trigger and audit events."""
    def active_policy(self, owner_id):
        row = db.session.execute(select(PolicyVersionRecord).where(
            PolicyVersionRecord.owner_id == owner_id).order_by(
                PolicyVersionRecord.version.desc()).limit(1)).scalar_one_or_none()
        return PolicyVersion(row.version, row.source, parse(row.source), _aware(row.created_at)) if row else None

    def accept_policy(self, owner_id, source, policy, created_at):
        try:
            db.session.execute(select(AccountRecord.account_id).where(
                AccountRecord.account_id == owner_id).with_for_update()).scalar_one()
            latest = db.session.execute(select(func.max(PolicyVersionRecord.version)).where(
                PolicyVersionRecord.owner_id == owner_id)).scalar_one() or 0
            row = PolicyVersionRecord(owner_id=owner_id, version=latest + 1,
                                      source=source, created_at=created_at)
            db.session.add(row)
            db.session.commit()
            return PolicyVersion(row.version, source, policy, created_at)
        except Exception:
            db.session.rollback()
            raise

    def is_triggered(self, owner_id):
        return db.session.get(OwnerLifecycleRecord, owner_id) is not None

    def trigger(self, owner_id):
        if not self.is_triggered(owner_id):
            db.session.add(OwnerLifecycleRecord(owner_id=owner_id, death_triggered_at=datetime.now(timezone.utc)))
            db.session.commit()

    def add_audit(self, record):
        db.session.add(AuditEventRecord(actor_id=record.actor_id, owner_id=record.owner_id,
            action=record.action, status=record.status, resource_id=record.resource_id,
            created_at=record.created_at))
        db.session.commit()

    def audits(self):
        rows = db.session.execute(select(AuditEventRecord).order_by(AuditEventRecord.event_id)).scalars()
        return tuple(AuditRecord(x.actor_id, x.owner_id, x.action, x.status, _aware(x.created_at), x.resource_id) for x in rows)


class SQLAlchemySummaryStore:
    def get(self, owner_id, entry_id):
        row = db.session.get(DerivedSummaryRecord, (owner_id, entry_id))
        return SummaryArtifact(row.owner_id, row.entry_id, row.text, row.source_digest) if row else None

    def put(self, artifact):
        row = db.session.get(DerivedSummaryRecord, (artifact.owner_id, artifact.entry_id))
        if row is None:
            row = DerivedSummaryRecord(owner_id=artifact.owner_id, entry_id=artifact.entry_id)
            db.session.add(row)
        row.text, row.source_digest = artifact.text, artifact.source_digest
        db.session.commit()


class SQLAlchemyOwnerConversationStore:
    """Persist only bounded user questions; answers/evidence are regenerated per request."""
    def start_or_load(self, owner_id, conversation_id):
        now = datetime.now(timezone.utc)
        if conversation_id is None:
            from uuid import uuid4
            conversation_id = uuid4().hex
            db.session.add(OwnerConversationRecord(conversation_id=conversation_id,
                                                   owner_id=owner_id, updated_at=now))
            db.session.commit()
            return conversation_id, ()
        row = db.session.get(OwnerConversationRecord, conversation_id)
        if row is None or row.owner_id != owner_id:
            raise ValueError("conversation is unavailable")
        questions = db.session.execute(select(OwnerQuestionRecord.question).where(
            OwnerQuestionRecord.conversation_id == conversation_id).order_by(
                OwnerQuestionRecord.question_id.desc()).limit(4)).scalars().all()
        row.updated_at = now
        db.session.commit()
        return conversation_id, tuple(reversed(questions))

    def record_question(self, owner_id, conversation_id, question):
        row = db.session.get(OwnerConversationRecord, conversation_id)
        if row is None or row.owner_id != owner_id:
            raise ValueError("conversation is unavailable")
        db.session.add(OwnerQuestionRecord(conversation_id=conversation_id,
                                           question=question[:500], created_at=datetime.now(timezone.utc)))
        row.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        overflow = db.session.execute(select(OwnerQuestionRecord).where(
            OwnerQuestionRecord.conversation_id == conversation_id).order_by(
                OwnerQuestionRecord.question_id.desc()).offset(4)).scalars().all()
        for item in overflow:
            db.session.delete(item)
        db.session.commit()
