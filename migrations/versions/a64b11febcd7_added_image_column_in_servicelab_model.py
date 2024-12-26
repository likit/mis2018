"""Added image column in ServiceLab model

Revision ID: a64b11febcd7
Revises: 1ee23d2a6182
Create Date: 2024-11-28 09:12:16.660490

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a64b11febcd7'
down_revision = '1ee23d2a6182'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_labs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_labs', schema=None) as batch_op:
        batch_op.drop_column('image')
    # ### end Alembic commands ###