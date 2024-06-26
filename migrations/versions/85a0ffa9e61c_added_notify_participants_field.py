"""added notify_participants field

Revision ID: 85a0ffa9e61c
Revises: cdf234b0242d
Create Date: 2023-05-24 14:59:28.946187

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85a0ffa9e61c'
down_revision = 'cdf234b0242d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('scheduler_room_reservations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notify_participants', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('scheduler_room_reservations', schema=None) as batch_op:
        batch_op.drop_column('notify_participants')

    # ### end Alembic commands ###
