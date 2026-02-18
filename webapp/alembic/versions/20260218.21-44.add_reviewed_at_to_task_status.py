"""add_reviewed_at_to_task_status

Revision ID: fb540271e53c
Revises: 3ba9006b379c
Create Date: 2026-02-18 21:44:17.419706

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb540271e53c'
down_revision = '3ba9006b379c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('task_statuses') as bop:
        bop.add_column(sa.Column('reviewed_at', sa.DateTime, nullable=True))


def downgrade():
    with op.batch_alter_table("task_statuses") as bop:
        bop.drop_column("reviewed_at")
