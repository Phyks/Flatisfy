# coding: utf-8
"""
This modules implements custom types in SQLAlchemy.
"""
from __future__ import absolute_import, print_function, unicode_literals

import json

import sqlalchemy.types as types


class StringyJSON(types.TypeDecorator):
    """
    Stores and retrieves JSON as TEXT for SQLite.

    From
    https://avacariu.me/articles/2016/compiling-json-as-text-for-sqlite-with-sqlalchemy.

    .. note :: The associated field is immutable. That is, changes to the data
    (typically, changing the value of a dict field) will not trigger an update
    on the SQL side upon ``commit`` as the reference to the object will not
    have been updated. One should force the update by forcing an update of the
    reference (by performing a ``copy`` operation on the dict for instance).
    """

    impl = types.TEXT

    def process_bind_param(self, value, dialect):
        """
        TODO
        """
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """
        TODO
        """
        if value is not None:
            value = json.loads(value)
        return value


# TypeEngine.with_variant says "use StringyJSON instead when
# connecting to 'sqlite'"
# pylint: disable=invalid-name
MagicJSON = types.JSON().with_variant(StringyJSON, 'sqlite')
