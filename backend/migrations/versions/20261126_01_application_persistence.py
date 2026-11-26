"""Persist append-only diary data, access state, summaries and owner context."""
from alembic import op
import sqlalchemy as sa

revision = "20261126_01"
down_revision = "20261121_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("diary_entries",
        sa.Column("owner_id", sa.String(64), sa.ForeignKey("accounts.account_id"), primary_key=True),
        sa.Column("entry_id", sa.String(64), primary_key=True),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source_timestamp", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.Text), sa.Column("recipient", sa.Text),
        sa.Column("previous_hash", sa.String(64), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.UniqueConstraint("owner_id", "sequence", name="uq_diary_owner_sequence"),
        sa.CheckConstraint("kind IN ('diary', 'letter')", name="ck_diary_kind"))
    op.create_index("ix_diary_owner_created", "diary_entries", ["owner_id", "created_at"])
    for table, field in (("diary_entry_names", "name"), ("diary_entry_topics", "topic")):
        op.create_table(table,
            sa.Column("owner_id", sa.String(64), primary_key=True),
            sa.Column("entry_id", sa.String(64), primary_key=True),
            sa.Column("ordinal", sa.Integer, primary_key=True),
            sa.Column(field, sa.Text, nullable=False),
            sa.ForeignKeyConstraint(["owner_id", "entry_id"], ["diary_entries.owner_id", "diary_entries.entry_id"]))
    op.create_table("derived_summaries",
        sa.Column("owner_id", sa.String(64), primary_key=True), sa.Column("entry_id", sa.String(64), primary_key=True),
        sa.Column("text", sa.Text, nullable=False), sa.Column("source_digest", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["owner_id", "entry_id"], ["diary_entries.owner_id", "diary_entries.entry_id"]))
    op.create_table("policy_versions",
        sa.Column("owner_id", sa.String(64), sa.ForeignKey("accounts.account_id"), primary_key=True),
        sa.Column("version", sa.Integer, primary_key=True), sa.Column("source", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("owner_lifecycle",
        sa.Column("owner_id", sa.String(64), sa.ForeignKey("accounts.account_id"), primary_key=True),
        sa.Column("death_triggered_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("audit_events",
        sa.Column("event_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("actor_id", sa.String(64), sa.ForeignKey("accounts.account_id"), nullable=False),
        sa.Column("owner_id", sa.String(64), sa.ForeignKey("accounts.account_id"), nullable=False),
        sa.Column("action", sa.String(64), nullable=False), sa.Column("status", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(128)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_audit_events_owner_id", "audit_events", ["owner_id"])
    op.create_table("owner_conversations",
        sa.Column("conversation_id", sa.String(32), primary_key=True),
        sa.Column("owner_id", sa.String(64), sa.ForeignKey("accounts.account_id"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_owner_conversations_owner_id", "owner_conversations", ["owner_id"])
    op.create_index("ix_owner_conversations_updated_at", "owner_conversations", ["updated_at"])
    op.create_table("owner_conversation_questions",
        sa.Column("question_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.String(32), sa.ForeignKey("owner_conversations.conversation_id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.String(500), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_owner_conversation_questions_conversation_id", "owner_conversation_questions", ["conversation_id"])


def downgrade():
    raise RuntimeError("Application persistence downgrade is disabled to protect user data.")
