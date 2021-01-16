"""Add flat position column

Revision ID: d21933db9ad8
Revises: 8155b83242eb
Create Date: 2021-02-08 16:26:37.190842

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.types as types
import json


class StringyJSON(types.TypeDecorator):
    """
    Stores and retrieves JSON as TEXT for SQLite.

    From
    https://avacariu.me/articles/2016/compiling-json-as-text-for-sqlite-with-sqlalchemy.

    .. note ::

        The associated field is immutable. That is, changes to the data
        (typically, changing the value of a dict field) will not trigger an
        update on the SQL side upon ``commit`` as the reference to the object
        will not have been updated. One should force the update by forcing an
        update of the reference (by performing a ``copy`` operation on the dict
        for instance).
    """

    impl = types.TEXT

    def process_bind_param(self, value, dialect):
        """
        Process the bound param, serialize the object to JSON before saving
        into database.
        """
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """
        Process the value fetched from the database, deserialize the JSON
        string before returning the object.
        """
        if value is not None:
            value = json.loads(value)
        return value


# TypeEngine.with_variant says "use StringyJSON instead when
# connecting to 'sqlite'"
# pylint: disable=locally-disabled,invalid-name
MagicJSON = types.JSON().with_variant(StringyJSON, "sqlite")

# revision identifiers, used by Alembic.
revision = "d21933db9ad8"
down_revision = "8155b83242eb"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("flats", sa.Column("flatisfy_position", MagicJSON, default=False))


def downgrade():
    op.drop_column("flats", "flatisfy_position")
