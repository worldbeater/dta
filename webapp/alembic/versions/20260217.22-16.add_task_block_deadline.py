"""add_task_block_deadline

Revision ID: 3ba9006b379c
Revises: a8e656f1b1df
Create Date: 2026-02-17 22:16:18.151846

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ba9006b379c'
down_revision = 'a8e656f1b1df'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('task_blocks') as bop:
        bop.add_column(sa.Column('deadline', sa.DateTime, nullable=True))


def downgrade():
    with op.batch_alter_table("task_blocks") as bop:
        bop.drop_column("deadline")
