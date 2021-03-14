# coding: utf-8
"""
This module contains functions related to the database.
"""
from __future__ import absolute_import, print_function, unicode_literals

import sqlite3

from contextlib import contextmanager

from sqlalchemy import event, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, SQLAlchemyError

import flatisfy.models.flat  # noqa: F401
from flatisfy.database.base import BASE
from flatisfy.database.whooshalchemy import IndexService


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    """
    Auto enable foreign keys for SQLite.
    """
    # Play well with other DB backends
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db(database_uri=None, search_db_uri=None):
    """
    Initialize the database, ensuring tables exist etc.

    :param database_uri: An URI describing an engine to use. Defaults to
        in-memory SQLite database.
    :param search_db_uri: Path to the Whoosh index file to use.
    :return: A tuple of an SQLAlchemy session maker and the created engine.
    """
    if database_uri is None:
        database_uri = "sqlite:///:memory:"

    engine = create_engine(database_uri)
    BASE.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)  # pylint: disable=locally-disabled,invalid-name

    if search_db_uri:
        index_service = IndexService(whoosh_base=search_db_uri)
        index_service.register_class(flatisfy.models.flat.Flat)

    @contextmanager
    def get_session():
        # pylint: disable=locally-disabled,line-too-long
        """
        Provide a transactional scope around a series of operations.

        From [1].
        [1]: http://docs.sqlalchemy.org/en/latest/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it.
        """
        # pylint: enable=line-too-long,locally-disabled
        session = Session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    return get_session
