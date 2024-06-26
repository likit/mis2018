"""Added GL, cost center, and internal order

Revision ID: de57e7d82b26
Revises: 9b3eb7509a20
Create Date: 2022-11-15 14:39:47.326000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'de57e7d82b26'
down_revision = '9b3eb7509a20'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('electronic_receipt_details', sa.Column('cost_center', sa.String(length=8), nullable=True))
    op.add_column('electronic_receipt_details', sa.Column('gl', sa.Integer(), nullable=True))
    op.add_column('electronic_receipt_details', sa.Column('internal_order', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('electronic_receipt_details', 'internal_order')
    op.drop_column('electronic_receipt_details', 'gl')
    op.drop_column('electronic_receipt_details', 'cost_center')
    # ### end Alembic commands ###
