"""Add persistent accounts and invitations without changing existing tables."""

from alembic import op
import sqlalchemy as sa


revision = "20261121_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "accounts",
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("person_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("account_id"),
        sa.UniqueConstraint("username", name="uq_accounts_username"),
        sa.UniqueConstraint("email", name="uq_accounts_email"),
        sa.UniqueConstraint("owner_id", "person_id", name="uq_accounts_owner_person"),
    )
    op.create_index("ix_accounts_owner_id", "accounts", ["owner_id"], unique=False)
    op.create_table(
        "invitations",
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("person_id", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["owner_id"], ["accounts.account_id"]),
        sa.PrimaryKeyConstraint("code_hash"),
    )
    op.create_index("ix_invitations_owner_id", "invitations", ["owner_id"], unique=False)


def downgrade():
    # Deliberately non-destructive: account history must not be dropped automatically.
    raise RuntimeError("Account persistence downgrade is intentionally disabled.")
