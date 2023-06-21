"""moved missions relationship from staff_seminar table to staff_seminar_attends table

Revision ID: 9f7bc092f15c
Revises: 19ed71216d91
Create Date: 2023-02-17 12:26:11.329440

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f7bc092f15c'
down_revision = '19ed71216d91'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_seminar_mission_assoc', sa.Column('seminar_attend_id', sa.Integer(), nullable=True))
    op.drop_constraint(u'staff_seminar_mission_assoc_seminar_id_fkey', 'staff_seminar_mission_assoc', type_='foreignkey')
    op.create_foreign_key(None, 'staff_seminar_mission_assoc', 'staff_seminar_attends', ['seminar_attend_id'], ['id'])
    op.drop_column('staff_seminar_mission_assoc', 'seminar_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_seminar_mission_assoc', sa.Column('seminar_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'staff_seminar_mission_assoc', type_='foreignkey')
    op.create_foreign_key(u'staff_seminar_mission_assoc_seminar_id_fkey', 'staff_seminar_mission_assoc', 'staff_seminar', ['seminar_id'], ['id'])
    op.drop_column('staff_seminar_mission_assoc', 'seminar_attend_id')
    # ### end Alembic commands ###