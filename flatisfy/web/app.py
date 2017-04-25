# coding: utf-8
"""
This module contains the definition of the Bottle web app.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import functools
import json
import logging
import os

import bottle
import canister

from flatisfy import database
from flatisfy.tools import DateAwareJSONEncoder
from flatisfy.web.routes import api as api_routes
from flatisfy.web.configplugin import ConfigPlugin
from flatisfy.web.dbplugin import DatabasePlugin


class QuietWSGIRefServer(bottle.WSGIRefServer):
    """
    Quiet implementation of Bottle built-in WSGIRefServer, as `Canister` is
    handling the logging through standard Python logging.
    """
    # pylint: disable=locally-disabled,too-few-public-methods
    quiet = True


def _serve_static_file(filename):
    """
    Helper function to serve static file.
    """
    return bottle.static_file(
        filename,
        root=os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "static"
        )
    )


def get_app(config):
    """
    Get a Bottle app instance with all the routes set-up.

    :return: The built bottle app.
    """
    get_session = database.init_db(config["database"])

    app = bottle.default_app()
    app.install(DatabasePlugin(get_session))
    app.install(ConfigPlugin(config))
    app.config.setdefault("canister.log_level", logging.root.level)
    app.config.setdefault("canister.log_path", None)
    app.config.setdefault("canister.debug", False)
    app.install(canister.Canister())
    # Use DateAwareJSONEncoder to dump JSON strings
    # From http://stackoverflow.com/questions/21282040/bottle-framework-how-to-return-datetime-in-json-response#comment55718456_21282666.  pylint: disable=locally-disabled,line-too-long
    bottle.install(
        bottle.JSONPlugin(
            json_dumps=functools.partial(json.dumps, cls=DateAwareJSONEncoder)
        )
    )

    # API v1 routes
    app.route("/api/v1/", "GET", api_routes.index_v1)

    app.route("/api/v1/time_to/places", "GET", api_routes.time_to_places_v1)

    app.route("/api/v1/flats", "GET", api_routes.flats_v1)
    app.route("/api/v1/flats/status/:status", "GET",
              api_routes.flats_by_status_v1)

    app.route("/api/v1/flat/:flat_id", "GET", api_routes.flat_v1)
    app.route("/api/v1/flat/:flat_id/status", "POST",
              api_routes.update_flat_status_v1)

    # Index
    app.route("/", "GET", lambda: _serve_static_file("index.html"))

    # Static files
    app.route(
        "/assets/<filename:path>", "GET",
        lambda filename: _serve_static_file("/assets/{}".format(filename))
    )

    return app
