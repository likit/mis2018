"""added some more models

Revision ID: 1a9deee603b9
Revises: 06267630a256
Create Date: 2023-04-26 23:46:00.273717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a9deee603b9'
down_revision = '06267630a256'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('complaint_priorities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('priority_text', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('complaint_statuses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('complaint_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('desc', sa.Text(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.Column('priority_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['priority_id'], ['complaint_priorities.id'], ),
    sa.ForeignKeyConstraint(['status'], ['complaint_statuses.id'], ),
    sa.ForeignKeyConstraint(['topic_id'], ['complaint_topics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('complaint_action_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('record_id', sa.Integer(), nullable=True),
    sa.Column('reviewer_id', sa.Integer(), nullable=True),
    sa.Column('review_comment', sa.Text(), nullable=True),
    sa.Column('approver_id', sa.Integer(), nullable=True),
    sa.Column('approved', sa.DateTime(timezone=True), nullable=True),
    sa.Column('approver_comment', sa.Text(), nullable=True),
    sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['approver_id'], ['complaint_admins.id'], ),
    sa.ForeignKeyConstraint(['record_id'], ['complaint_records.id'], ),
    sa.ForeignKeyConstraint(['reviewer_id'], ['complaint_admins.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('complaint_action_records')
    op.drop_table('complaint_records')
    op.drop_table('complaint_statuses')
    op.drop_table('complaint_priorities')
    # ### end Alembic commands ###