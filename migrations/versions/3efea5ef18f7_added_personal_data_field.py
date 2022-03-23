"""added personal data field

Revision ID: 3efea5ef18f7
Revises: 32ea031f6871
Create Date: 2022-03-22 01:31:29.903000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3efea5ef18f7'
down_revision = '32ea031f6871'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('db_datasets', sa.Column('personal', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('db_datasets', 'personal')
    # ### end Alembic commands ###