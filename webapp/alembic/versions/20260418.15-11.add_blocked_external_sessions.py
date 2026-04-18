"""add_blocked_external_sessions

Revision ID: f077131d8a66
Revises: 01b61c7a1248
Create Date: 2026-04-18 15:11:26.125960

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f077131d8a66'
down_revision = '01b61c7a1248'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "blocked_external_sessions",
        sa.Column("sid", sa.String, primary_key=True, nullable=False),
        sa.Column("time", sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table("blocked_external_sessions")
