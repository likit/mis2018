"""added pubmonth to research pub model

Revision ID: 37647a14902d
Revises: 363a00ba2a77
Create Date: 2018-05-15 15:48:59.382158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '37647a14902d'
down_revision = '363a00ba2a77'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('research_pub', sa.Column('pubmonth', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('research_pub', 'pubmonth')
    # ### end Alembic commands ###