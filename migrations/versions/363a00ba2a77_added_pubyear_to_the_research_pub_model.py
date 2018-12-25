"""added pubyear to the research pub model

Revision ID: 363a00ba2a77
Revises: 70aac3b05b39
Create Date: 2018-05-15 15:44:23.407319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '363a00ba2a77'
down_revision = '70aac3b05b39'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('research_pub', sa.Column('pubyear', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('research_pub', 'pubyear')
    # ### end Alembic commands ###