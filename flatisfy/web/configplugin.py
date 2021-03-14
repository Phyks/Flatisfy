# coding: utf-8
"""
This module contains a Bottle plugin to pass the config argument to any route
which needs it.

This module is heavily based on code from
[Bottle-SQLAlchemy](https://github.com/iurisilvio/bottle-sqlalchemy) which is
licensed under MIT license.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import functools
import inspect

import bottle


class ConfigPlugin(object):
    """
    A Bottle plugin to automatically pass the config object to the routes
    specifying they need it.
    """

    name = "config"
    api = 2
    KEYWORD = "config"

    def __init__(self, config):
        """
        :param config: The config object to pass.
        """
        self.config = config

    def setup(self, app):  # pylint: disable=locally-disabled,no-self-use
        """
        Make sure that other installed plugins don't affect the same
        keyword argument and check if metadata is available.
        """
        for other in app.plugins:
            if not isinstance(other, ConfigPlugin):
                continue
            else:
                raise bottle.PluginError("Found another conflicting Config plugin.")

    def apply(self, callback, route):
        """
        Method called on route invocation. Should apply some transformations to
        the route prior to returing it.

        We check the presence of ``self.KEYWORD`` in the route signature and
        replace the route callback by a partial invocation where we replaced
        this argument by a valid config object.
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
        kwargs = {}
        kwargs[self.KEYWORD] = self.config
        return functools.partial(callback, **kwargs)


Plugin = ConfigPlugin
