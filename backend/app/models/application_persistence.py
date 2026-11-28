"""Durable application records; immutable diary evidence is append-only."""
from sqlalchemy import event
from app.extensions import db


class DiaryEntryRecord(db.Model):
    __tablename__ = "diary_entries"
    __table_args__ = (
        db.UniqueConstraint("owner_id", "sequence", name="uq_diary_owner_sequence"),
        db.CheckConstraint("kind IN ('diary', 'letter')", name="ck_diary_kind"),
        db.Index("ix_diary_owner_created", "owner_id", "created_at"),
    )
    owner_id = db.Column(db.String(64), db.ForeignKey("accounts.account_id"), primary_key=True)
    entry_id = db.Column(db.String(64), primary_key=True)
    sequence = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(16), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source_timestamp = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    title = db.Column(db.Text)
    recipient = db.Column(db.Text)
    release_date = db.Column(db.Date)
    previous_hash = db.Column(db.String(64), nullable=False)
    digest = db.Column(db.String(64), nullable=False)
    names = db.relationship("DiaryEntryNameRecord", cascade="all, delete-orphan", order_by="DiaryEntryNameRecord.ordinal")
    topics = db.relationship("DiaryEntryTopicRecord", cascade="all, delete-orphan", order_by="DiaryEntryTopicRecord.ordinal")


class DiaryEntryNameRecord(db.Model):
    __tablename__ = "diary_entry_names"
    owner_id = db.Column(db.String(64), primary_key=True)
    entry_id = db.Column(db.String(64), primary_key=True)
    ordinal = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint(["owner_id", "entry_id"], ["diary_entries.owner_id", "diary_entries.entry_id"]),)


class DiaryEntryTopicRecord(db.Model):
    __tablename__ = "diary_entry_topics"
    owner_id = db.Column(db.String(64), primary_key=True)
    entry_id = db.Column(db.String(64), primary_key=True)
    ordinal = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.Text, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint(["owner_id", "entry_id"], ["diary_entries.owner_id", "diary_entries.entry_id"]),)


class DerivedSummaryRecord(db.Model):
    __tablename__ = "derived_summaries"
    owner_id = db.Column(db.String(64), primary_key=True)
    entry_id = db.Column(db.String(64), primary_key=True)
    text = db.Column(db.Text, nullable=False)
    source_digest = db.Column(db.String(64), nullable=False)
    __table_args__ = (db.ForeignKeyConstraint(["owner_id", "entry_id"], ["diary_entries.owner_id", "diary_entries.entry_id"]),)


class PolicyVersionRecord(db.Model):
    __tablename__ = "policy_versions"
    owner_id = db.Column(db.String(64), db.ForeignKey("accounts.account_id"), primary_key=True)
    version = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)


class OwnerLifecycleRecord(db.Model):
    __tablename__ = "owner_lifecycle"
    owner_id = db.Column(db.String(64), db.ForeignKey("accounts.account_id"), primary_key=True)
    death_triggered_at = db.Column(db.DateTime(timezone=True), nullable=False)


class AuditEventRecord(db.Model):
    __tablename__ = "audit_events"
    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    actor_id = db.Column(db.String(64), db.ForeignKey("accounts.account_id"), nullable=False)
    owner_id = db.Column(db.String(64), db.ForeignKey("accounts.account_id"), nullable=False, index=True)
    action = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(64), nullable=False)
    resource_id = db.Column(db.String(128))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)


class OwnerConversationRecord(db.Model):
    __tablename__ = "owner_conversations"
    conversation_id = db.Column(db.String(32), primary_key=True)
    owner_id = db.Column(db.String(64), db.ForeignKey("accounts.account_id"), nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)


class OwnerQuestionRecord(db.Model):
    __tablename__ = "owner_conversation_questions"
    question_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.String(32), db.ForeignKey("owner_conversations.conversation_id", ondelete="CASCADE"), nullable=False, index=True)
    question = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)


def _reject_entry_mutation(mapper, connection, target):
    raise ValueError("Diary evidence is append-only and cannot be changed or deleted.")


for _immutable_model in (
    DiaryEntryRecord, DiaryEntryNameRecord, DiaryEntryTopicRecord,
    PolicyVersionRecord, OwnerLifecycleRecord, AuditEventRecord,
):
    event.listen(_immutable_model, "before_update", _reject_entry_mutation)
    event.listen(_immutable_model, "before_delete", _reject_entry_mutation)
