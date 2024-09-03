"""Update product model

Revision ID: 179b2dd6bbaa
Revises: 8fec250e0f88
Create Date: 2024-09-03 04:25:45.539798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '179b2dd6bbaa'
down_revision = '8fec250e0f88'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mpesa_code', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_column('mpesa_code')

    # ### end Alembic commands ###
