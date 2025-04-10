"""Added type_id and type column in ServiceCustomerInfo model

Revision ID: e36b963d567f
Revises: a8b4b027891a
Create Date: 2024-11-13 11:19:05.105758

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e36b963d567f'
down_revision = 'a8b4b027891a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('topic_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'service_customer_types', ['topic_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('topic_id')
    # ### end Alembic commands ###
