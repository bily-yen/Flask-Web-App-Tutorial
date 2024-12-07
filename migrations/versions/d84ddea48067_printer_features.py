"""printer features

Revision ID: d84ddea48067
Revises: 7b9427066679
Create Date: 2024-12-06 20:17:09.281888

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd84ddea48067'
down_revision = '7b9427066679'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('print_speed', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('resolution', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('connectivity', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('color', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('type', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('printers', schema=None) as batch_op:
        batch_op.drop_column('type')
        batch_op.drop_column('color')
        batch_op.drop_column('connectivity')
        batch_op.drop_column('resolution')
        batch_op.drop_column('print_speed')

    # ### end Alembic commands ###
