"""add_task_blocks

Revision ID: a8e656f1b1df
Revises: 2a3942c432db
Create Date: 2026-02-01 14:02:29.220477

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8e656f1b1df'
down_revision = '2a3942c432db'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "task_blocks",
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("title", sa.String, nullable=False),
    )
    with op.batch_alter_table('tasks') as bop:
        bop.add_column(sa.Column('block', sa.Integer, nullable=True))
        bop.create_foreign_key('fk_tasks_block', 'task_blocks', ['block'], ['id'])


def downgrade():
    with op.batch_alter_table("tasks") as bop:
        bop.drop_constraint("fk_tasks_block", type_="foreignkey")
        bop.drop_column("block")
    op.drop_table("task_blocks")
