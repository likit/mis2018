"""Deleted nullable in tag column of ComplaintTag model

Revision ID: c31b170fce18
Revises: f3529705897e
Create Date: 2024-05-16 09:17:55.068645

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c31b170fce18'
down_revision = 'f3529705897e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('complaint_tags', schema=None) as batch_op:
        batch_op.alter_column('tag',
               existing_type=sa.VARCHAR(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('complaint_tags', schema=None) as batch_op:
        batch_op.alter_column('tag',
               existing_type=sa.VARCHAR(),
               nullable=False)

    # ### end Alembic commands ###