"""added maintainer id field

Revision ID: 8f9eab837b3b
Revises: 232ce2eb1b24
Create Date: 2022-02-25 13:24:50.230615

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f9eab837b3b'
down_revision = '232ce2eb1b24'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('db_datasets', sa.Column('maintainer_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'db_datasets', 'staff_account', ['maintainer_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'db_datasets', type_='foreignkey')
    op.drop_column('db_datasets', 'maintainer_id')
    # ### end Alembic commands ###
