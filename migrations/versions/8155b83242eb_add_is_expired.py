"""Add is_expired

Revision ID: 8155b83242eb
Revises:
Create Date: 2018-10-16 22:51:25.442678

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8155b83242eb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'flats',
        sa.Column('is_expired', sa.Boolean(), default=False)
    )


def downgrade():
    op.drop_column(
        'flats',
        'is_expired'
    )
