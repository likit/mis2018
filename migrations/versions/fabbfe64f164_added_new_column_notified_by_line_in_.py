"""added new column notified_by_line in table StaffLeaveApprover

Revision ID: fabbfe64f164
Revises: f37440b63a42
Create Date: 2020-08-25 09:27:22.245689

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fabbfe64f164'
down_revision = 'f37440b63a42'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_leave_approvers', sa.Column('notified_by_line', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('staff_leave_approvers', 'notified_by_line')
    # ### end Alembic commands ###
