"""Persist required letter release dates."""
from alembic import op
import sqlalchemy as sa

revision = "20261128_01"
down_revision = "20261126_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("diary_entries", sa.Column("release_date", sa.Date(), nullable=True))


def downgrade():
    op.drop_column("diary_entries", "release_date")
