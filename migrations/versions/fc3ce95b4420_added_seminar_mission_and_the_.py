"""added seminar mission and the association table

Revision ID: fc3ce95b4420
Revises: b8dc7258ad84
Create Date: 2022-09-12 14:09:18.760686

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fc3ce95b4420'
down_revision = 'b8dc7258ad84'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('staff_seminar_missions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('mission', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('staff_seminar_mission_assoc',
    sa.Column('seminar_id', sa.Integer(), nullable=True),
    sa.Column('seminar_mission_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['seminar_id'], ['staff_seminar.id'], ),
    sa.ForeignKeyConstraint(['seminar_mission_id'], ['staff_seminar_missions.id'], )
    )
    op.create_table('seminar_approval_attend_assoc',
    sa.Column('attend_id', sa.Integer(), nullable=False),
    sa.Column('approval_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['approval_id'], ['staff_seminar_approvals.id'], ),
    sa.ForeignKeyConstraint(['attend_id'], ['staff_seminar_attends.id'], ),
    sa.PrimaryKeyConstraint('attend_id', 'approval_id')
    )
    op.drop_column(u'staff_seminar', 'mission')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'staff_seminar', sa.Column('mission', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_table('seminar_approval_attend_assoc')
    op.drop_table('staff_seminar_mission_assoc')
    op.drop_table('staff_seminar_missions')
    # ### end Alembic commands ###