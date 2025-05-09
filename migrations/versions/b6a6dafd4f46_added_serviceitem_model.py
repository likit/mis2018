"""Added ServiceItem model

Revision ID: b6a6dafd4f46
Revises: 2b0916bab618
Create Date: 2025-03-31 13:46:19.408728

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b6a6dafd4f46'
down_revision = '2b0916bab618'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('service_items',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('item', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('service_items')
    # ### end Alembic commands ###
