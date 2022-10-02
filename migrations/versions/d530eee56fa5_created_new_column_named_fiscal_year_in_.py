"""created new column named fiscal_year in table staff_leave_used_quota

Revision ID: d530eee56fa5
Revises: 305b47f068f2
Create Date: 2022-08-22 14:00:59.148752

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd530eee56fa5'
down_revision = '305b47f068f2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_leave_used_quota', sa.Column('fiscal_year', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('staff_leave_used_quota', 'fiscal_year')
    # ### end Alembic commands ###