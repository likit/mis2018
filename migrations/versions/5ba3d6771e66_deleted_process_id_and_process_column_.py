"""Deleted process_id and process column in SoftwareRequestDetail model

Revision ID: 5ba3d6771e66
Revises: 5a4735a6bbb5
Create Date: 2025-03-21 14:21:03.412206

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5ba3d6771e66'
down_revision = '5a4735a6bbb5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('software_request_details', schema=None) as batch_op:
        batch_op.drop_constraint('software_request_details_process_id_fkey', type_='foreignkey')
        batch_op.drop_column('process_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('software_request_details', schema=None) as batch_op:
        batch_op.add_column(sa.Column('process_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('software_request_details_process_id_fkey', 'db_processes', ['process_id'], ['id'])
    # ### end Alembic commands ###
