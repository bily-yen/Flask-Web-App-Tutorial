"""Add printer relationship to order items

Revision ID: 3b0edc6d6ed0
Revises: a041b1e10813
Create Date: 2024-10-22 12:03:11.899202

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b0edc6d6ed0'
down_revision = 'a041b1e10813'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transaction_products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('printer_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'printers', ['printer_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transaction_products', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('printer_id')

    # ### end Alembic commands ###
