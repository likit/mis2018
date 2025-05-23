"""Added pdf_file column in ServiceRequest model

Revision ID: ffb97545b5b7
Revises: c83fa5544e96
Create Date: 2024-10-22 11:33:44.936921

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ffb97545b5b7'
down_revision = 'c83fa5544e96'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pdf_file', sa.LargeBinary(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.drop_column('pdf_file')
    # ### end Alembic commands ###
