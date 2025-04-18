"""Added activity and activity_id column in SoftwareRequestDetail model

Revision ID: f94e036e17f6
Revises: 92a711ae4d91
Create Date: 2025-04-17 13:53:18.583783

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f94e036e17f6'
down_revision = '92a711ae4d91'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('software_request_details', schema=None) as batch_op:
        batch_op.add_column(sa.Column('activity_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'strategy_activities', ['activity_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('software_request_details', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('activity_id')
    # ### end Alembic commands ###
