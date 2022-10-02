"""name of type

Revision ID: fa5893033201
Revises: 08a03f1ab52e
Create Date: 2022-06-27 11:28:59.867000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa5893033201'
down_revision = '08a03f1ab52e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('procurement_requires', sa.Column('desc', sa.Text(), nullable=True))
    op.add_column('procurement_requires', sa.Column('notice_date', sa.Date(), nullable=True))
    op.add_column('procurement_requires', sa.Column('record_id', sa.Integer(), nullable=True))
    op.add_column('procurement_requires', sa.Column('service_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'procurement_requires', 'procurement_details', ['service_id'], ['id'])
    op.create_foreign_key(None, 'procurement_requires', 'procurement_records', ['record_id'], ['id'])
    op.drop_column('procurement_requires', 'explan')
    op.drop_column('procurement_requires', 'start_date')
    op.drop_column('procurement_requires', 'service')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('procurement_requires', sa.Column('service', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('procurement_requires', sa.Column('start_date', sa.DATE(), autoincrement=False, nullable=False))
    op.add_column('procurement_requires', sa.Column('explan', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'procurement_requires', type_='foreignkey')
    op.drop_constraint(None, 'procurement_requires', type_='foreignkey')
    op.drop_column('procurement_requires', 'service_id')
    op.drop_column('procurement_requires', 'record_id')
    op.drop_column('procurement_requires', 'notice_date')
    op.drop_column('procurement_requires', 'desc')
    # ### end Alembic commands ###