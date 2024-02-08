"""deleted year column in PAFunctionalCompetencyRound table

Revision ID: 2f239b2ab9d9
Revises: f7b5b69d4b81
Create Date: 2023-11-22 09:18:00.802949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f239b2ab9d9'
down_revision = 'f7b5b69d4b81'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pa_functional_competency_round', schema=None) as batch_op:
        batch_op.drop_column('year')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pa_functional_competency_round', schema=None) as batch_op:
        batch_op.add_column(sa.Column('year', sa.NUMERIC(), autoincrement=False, nullable=True))

    # ### end Alembic commands ###