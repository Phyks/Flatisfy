# coding: utf-8
"""
This module contains the definition of the Bottle web app.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import os

import bottle

from flatisfy import database
from flatisfy.web.routes import api as api_routes
from flatisfy.web.dbplugin import DatabasePlugin


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

    # API v1 routes
    app.route("/api/v1/", "GET", api_routes.index_v1)
    app.route("/api/v1/flats", "GET", api_routes.flats_v1)
    app.route("/api/v1/flat/:id", "GET", api_routes.flat_v1)

    # Index
    app.route("/", "GET", lambda: _serve_static_file("index.html"))

    # Static files
    app.route("/static/<filename:path>", "GET", _serve_static_file)

    return app
