"""Added assignee_id and assignee in ComplaintRecord model

Revision ID: 466af8c17187
Revises: 3bc72d91200d
Create Date: 2024-06-21 10:50:53.720510

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '466af8c17187'
down_revision = '3bc72d91200d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('complaint_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'complaint_admins', ['assigned_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('complaint_records', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('assigned_id')

    # ### end Alembic commands ###
