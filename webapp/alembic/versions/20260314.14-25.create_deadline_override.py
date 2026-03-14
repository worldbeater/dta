"""create_deadline_override

Revision ID: 01b61c7a1248
Revises: fb540271e53c
Create Date: 2026-03-14 14:25:34.631726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01b61c7a1248'
down_revision = 'fb540271e53c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'deadline_overrides',
        sa.Column("student", sa.Integer, sa.ForeignKey("students.id"), nullable=False, primary_key=True),
        sa.Column("block", sa.Integer, sa.ForeignKey("task_blocks.id"), nullable=False, primary_key=True),
        sa.Column("deadline", sa.DateTime, nullable=False),
        sa.Column("reason", sa.String, nullable=False),
        sa.Column("teacher", sa.Integer, sa.ForeignKey("students.id"), nullable=False),
    )


def downgrade():
    op.drop_table('deadline_overrides')
