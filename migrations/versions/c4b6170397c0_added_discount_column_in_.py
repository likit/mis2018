"""Added discount column in ServiceQuotation model

Revision ID: c4b6170397c0
Revises: 16807d14aaa0
Create Date: 2025-07-08 10:16:13.364251

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c4b6170397c0'
down_revision = '16807d14aaa0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_quotation_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_quotation_items', schema=None) as batch_op:
        batch_op.drop_column('discount')
    # ### end Alembic commands ###
