"""Added fax_no column in ServiceCustomerInfo model

Revision ID: 37f0b36a0446
Revises: 8991a34d32ee
Create Date: 2024-11-14 08:37:36.760409

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '37f0b36a0446'
down_revision = '8991a34d32ee'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fax_no', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.drop_column('fax_no')
    # ### end Alembic commands ###