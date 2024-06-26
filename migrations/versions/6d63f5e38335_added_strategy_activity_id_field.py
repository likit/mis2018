"""added strategy activity id field

Revision ID: 6d63f5e38335
Revises: 29d79440af17
Create Date: 2024-01-16 16:19:13.967259

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d63f5e38335'
down_revision = '29d79440af17'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pa_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('strategy_activity_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'strategy_activities', ['strategy_activity_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pa_items', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('strategy_activity_id')

    # ### end Alembic commands ###
