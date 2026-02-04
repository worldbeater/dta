"""add_reviewer_to_task_status

Revision ID: 2a3942c432db
Revises: 3782564289c1
Create Date: 2026-02-01 13:22:32.287727

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a3942c432db'
down_revision = '3782564289c1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('task_statuses') as bop:
        bop.add_column(sa.Column('reviewer', sa.Integer, nullable=True))
        bop.create_foreign_key('fk_task_statuses_reviewer', 'students', ['reviewer'], ['id'])


def downgrade():
    with op.batch_alter_table("task_statuses") as bop:
        bop.drop_constraint("fk_task_statuses_reviewer", type_="foreignkey")
        bop.drop_column("reviewer")
