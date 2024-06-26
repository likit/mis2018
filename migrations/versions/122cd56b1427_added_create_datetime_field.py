"""added create datetime field

Revision ID: 122cd56b1427
Revises: 5fd2e62e5b9c
Create Date: 2021-05-22 09:43:46.488430

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '122cd56b1427'
down_revision = '5fd2e62e5b9c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('doc_rounds', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('doc_rounds', 'created_at')
    # ### end Alembic commands ###
