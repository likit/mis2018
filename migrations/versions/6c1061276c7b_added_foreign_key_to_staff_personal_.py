"""added foreign key to staff personal info model

Revision ID: 6c1061276c7b
Revises: d0396e98c7bd
Create Date: 2018-04-17 15:17:51.958046

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c1061276c7b'
down_revision = 'd0396e98c7bd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_personal_info', sa.Column('staff_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'staff_personal_info', 'staff_account', ['staff_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'staff_personal_info', type_='foreignkey')
    op.drop_column('staff_personal_info', 'staff_id')
    # ### end Alembic commands ###
