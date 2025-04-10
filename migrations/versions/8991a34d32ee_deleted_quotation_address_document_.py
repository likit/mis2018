"""Deleted quotation_address, document_address, taxpayer_identification_no and deliverey_phone_number column in ServiceCustomerInfo model

Revision ID: 8991a34d32ee
Revises: 320a206ed17b
Create Date: 2024-11-13 16:21:10.985779

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8991a34d32ee'
down_revision = '320a206ed17b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.drop_column('delivery_phone_number')
        batch_op.drop_column('taxpayer_identification_no')
        batch_op.drop_column('document_address')
        batch_op.drop_column('quotation_address')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quotation_address', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('document_address', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('taxpayer_identification_no', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('delivery_phone_number', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
