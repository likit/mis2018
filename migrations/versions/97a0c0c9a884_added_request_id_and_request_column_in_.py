"""Added request_id and request column in ServiceQuotation model

Revision ID: 97a0c0c9a884
Revises: a8f3d826a2ef
Create Date: 2024-11-21 19:39:23.376596

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '97a0c0c9a884'
down_revision = 'a8f3d826a2ef'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_quotations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('request_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'service_requests', ['request_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_quotations', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('request_id')
    # ### end Alembic commands ###