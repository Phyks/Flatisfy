"""Add flat INSEE column

Revision ID: 9e58c66f1ac1
Revises: d21933db9ad8
Create Date: 2021-02-08 16:31:18.961186

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9e58c66f1ac1"
down_revision = "d21933db9ad8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("postal_codes", sa.Column("insee_code", sa.String()))


def downgrade():
    op.drop_column("postal_codes", "insee_code")
