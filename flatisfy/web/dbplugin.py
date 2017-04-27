# coding: utf-8
"""
This module contains a Bottle plugin to pass the database argument to any route
which needs it.

This module is heavily based on code from
[Bottle-SQLAlchemy](https://github.com/iurisilvio/bottle-sqlalchemy) which is
licensed under MIT license.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import inspect

import bottle


class DatabasePlugin(object):
    """
    A Bottle plugin to automatically pass an SQLAlchemy database session object
    to the routes specifying they need it.
    """
    name = 'database'
    api = 2
    KEYWORD = "db"

    def __init__(self, get_session):
        """
        :param create_session: SQLAlchemy session maker created with the
                'sessionmaker' function. Will create its own if undefined.
        """
        self.get_session = get_session

    def setup(self, app):  # pylint: disable=locally-disabled,no-self-use
        """
        Make sure that other installed plugins don't affect the same
        keyword argument and check if metadata is available.
        """
        for other in app.plugins:
            if not isinstance(other, DatabasePlugin):
                continue
            else:
                raise bottle.PluginError(
                    "Found another conflicting Database plugin."
                )

    def apply(self, callback, route):
        """
        Method called on route invocation. Should apply some transformations to
        the route prior to returing it.

        We check the presence of ``self.KEYWORD`` in the route signature and
        replace the route callback by a partial invocation where we replaced
        this argument by a valid SQLAlchemy session.
        """
        # Check whether the route needs a valid db session or not.
        try:
            callback_args = inspect.signature(route.callback).parameters
        except AttributeError:
            # inspect.signature does not exist on older Python
            callback_args = inspect.getargspec(route.callback).args

        if self.KEYWORD not in callback_args:
            # If no need for a db session, call the route callback
            return callback
        def wrapper(*args, **kwargs):
            """
            Wrap the callback in a call to get_session.
            """
            with self.get_session() as session:
                # Get a db session and pass it to the callback
                kwargs[self.KEYWORD] = session
                return callback(*args, **kwargs)
        return wrapper


Plugin = DatabasePlugin
