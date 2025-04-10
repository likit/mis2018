"""Added discount column in ServiceInvoice model

Revision ID: 93a3f2ffef66
Revises: 86938362bcf9
Create Date: 2025-04-01 15:32:22.888000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '93a3f2ffef66'
down_revision = '86938362bcf9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_invoice_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_invoice_items', schema=None) as batch_op:
        batch_op.drop_column('discount')
    # ### end Alembic commands ###
