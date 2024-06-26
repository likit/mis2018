"""deleted country column in table staff_seminar

Revision ID: cd57ca8f5d01
Revises: 391031663214
Create Date: 2022-07-08 09:36:41.822562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd57ca8f5d01'
down_revision = '391031663214'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('staff_seminar', 'country')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_seminar', sa.Column('country', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
