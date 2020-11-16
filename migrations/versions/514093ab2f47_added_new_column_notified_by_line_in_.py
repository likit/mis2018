"""added new column notified by line in table StaffAccount

Revision ID: 514093ab2f47
Revises: 002806480308
Create Date: 2020-08-14 13:56:40.194503

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '514093ab2f47'
down_revision = '002806480308'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_account', sa.Column('notified_by_line', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('staff_account', 'notified_by_line')
    # ### end Alembic commands ###