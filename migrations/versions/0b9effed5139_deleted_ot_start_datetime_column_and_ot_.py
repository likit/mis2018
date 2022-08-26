"""deleted ot_start_datetime column and ot_end_datetime column in table OtCompensationRate

Revision ID: 0b9effed5139
Revises: 1a8e2214359f
Create Date: 2021-11-08 23:06:30.340934

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0b9effed5139'
down_revision = '1a8e2214359f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ot_compensation_rate', 'ot_start_datetime')
    op.drop_column('ot_compensation_rate', 'ot_end_datetime')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ot_compensation_rate', sa.Column('ot_end_datetime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('ot_compensation_rate', sa.Column('ot_start_datetime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    # ### end Alembic commands ###