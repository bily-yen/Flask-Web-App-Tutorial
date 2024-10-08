"""Describe your migration here

Revision ID: 303eb62d6c0b
Revises: 7b82574d9027
Create Date: 2024-09-03 02:12:00.814687

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '303eb62d6c0b'
down_revision = '7b82574d9027'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.alter_column('image',
               existing_type=sa.BLOB(),
               type_=sa.String(length=1000),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.alter_column('image',
               existing_type=sa.String(length=1000),
               type_=sa.BLOB(),
               existing_nullable=True)

    # ### end Alembic commands ###
