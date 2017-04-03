# coding: utf-8
"""
This module contains a Bottle plugin to pass the database argument to any route
which needs it.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import functools
import inspect

import bottle


class DatabasePlugin(object):
    name = 'database'
    api = 2
    KEYWORD = "db"

    def __init__(self, get_session):
        """
        :param keyword: Keyword used to inject session database in a route
        :param create_session: SQLAlchemy session maker created with the
                'sessionmaker' function. Will create its own if undefined.
        """
        self.get_session = get_session

    def setup(self, app):
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
        try:
            callback_args = inspect.signature(route.callback).parameters
        except AttributeError:
            # inspect.signature does not exist on older Python
            callback_args = inspect.getargspec(route.callback).args

        if self.KEYWORD not in callback_args:
            return callback
        else:
            with self.get_session() as session:
                kwargs = {}
                kwargs[self.KEYWORD] = session
                return functools.partial(callback, **kwargs)


Plugin = DatabasePlugin
