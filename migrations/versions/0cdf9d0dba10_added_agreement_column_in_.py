"""Added agreement column in ComplaintRecord model

Revision ID: 0cdf9d0dba10
Revises: b8cdd57409fb
Create Date: 2024-04-04 09:17:54.002076

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0cdf9d0dba10'
down_revision = 'b8cdd57409fb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('complaint_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agreement', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('complaint_records', schema=None) as batch_op:
        batch_op.drop_column('agreement')

    # ### end Alembic commands ###