"""Added type_id and type column in ServiceCustomerContact model

Revision ID: 936fb014af61
Revises: b59259b856d6
Create Date: 2024-11-14 10:02:13.927501

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '936fb014af61'
down_revision = 'b59259b856d6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_contacts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'service_customer_contact_types', ['type_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_contacts', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('type_id')
    # ### end Alembic commands ###
