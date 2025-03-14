"""Added admin_id and admin column in ServicePayment, ServiceReceipt, ServiceInvoice, ServiceResult model

Revision ID: 2fb721bb05ca
Revises: ebcb9805df80
Create Date: 2024-11-21 11:26:36.538874

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2fb721bb05ca'
down_revision = 'ebcb9805df80'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'staff_account', ['admin_id'], ['id'])

    with op.batch_alter_table('service_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'staff_account', ['admin_id'], ['id'])

    with op.batch_alter_table('service_receipts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'staff_account', ['admin_id'], ['id'])

    with op.batch_alter_table('service_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'staff_account', ['admin_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_results', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('admin_id')

    with op.batch_alter_table('service_receipts', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('admin_id')

    with op.batch_alter_table('service_payments', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('admin_id')

    with op.batch_alter_table('service_invoices', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('admin_id')
    # ### end Alembic commands ###
