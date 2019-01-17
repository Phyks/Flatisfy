# coding: utf-8
"""
This module contains the definition of the Bottle web app.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import functools
import json
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

    def run(self, app):
        app.log.info(
            'Server is now up and ready! Listening on %s:%s.' %
            (self.host, self.port)
        )
        super(QuietWSGIRefServer, self).run(app)


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
    get_session = database.init_db(config["database"], config["search_index"])

    app = bottle.Bottle()
    app.install(DatabasePlugin(get_session))
    app.install(ConfigPlugin(config))
    app.config.setdefault("canister.log_level", "DISABLED")
    app.config.setdefault("canister.log_path", False)
    app.config.setdefault("canister.debug", False)
    app.install(canister.Canister())
    # Use DateAwareJSONEncoder to dump JSON strings
    # From http://stackoverflow.com/questions/21282040/bottle-framework-how-to-return-datetime-in-json-response#comment55718456_21282666.  pylint: disable=locally-disabled,line-too-long
    app.install(
        bottle.JSONPlugin(
            json_dumps=functools.partial(json.dumps, cls=DateAwareJSONEncoder)
        )
    )

    # Enable CORS
    @app.hook('after_request')
    def enable_cors():
        """
        Add CORS headers at each request.
        """
        # The str() call is required as we import unicode_literal and WSGI
        # headers list should have plain str type.
        bottle.response.headers[str('Access-Control-Allow-Origin')] = str('*')
        bottle.response.headers[str('Access-Control-Allow-Methods')] = str(
            'PUT, GET, POST, DELETE, OPTIONS, PATCH'
        )
        bottle.response.headers[str('Access-Control-Allow-Headers')] = str(
            'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        )

    # API v1 routes
    app.route("/api/v1", ["GET", "OPTIONS"], api_routes.index_v1)

    app.route("/api/v1/time_to_places", ["GET", "OPTIONS"],
              api_routes.time_to_places_v1)

    app.route("/api/v1/flats", ["GET", "OPTIONS"], api_routes.flats_v1)
    app.route("/api/v1/flats/:flat_id", ["GET", "OPTIONS"], api_routes.flat_v1)
    app.route("/api/v1/flats/:flat_id", ["PATCH", "OPTIONS"],
              api_routes.update_flat_v1)

    app.route("/api/v1/ics/visits.ics", ["GET", "OPTIONS"],
              api_routes.ics_feed_v1)

    app.route("/api/v1/search", ["POST", "OPTIONS"], api_routes.search_v1)

    app.route("/api/v1/opendata", ["GET", "OPTIONS"], api_routes.opendata_index_v1)
    app.route("/api/v1/opendata/postal_codes", ["GET", "OPTIONS"],
              api_routes.opendata_postal_codes_v1)

    app.route("/api/v1/metadata", ["GET", "OPTIONS"], api_routes.metadata_v1)

    # Index
    app.route("/", "GET", lambda: _serve_static_file("index.html"))

    # Static files
    app.route("/favicon.ico", "GET",
              lambda: _serve_static_file("favicon.ico"))
    app.route(
        "/assets/<filename:path>", "GET",
        lambda filename: _serve_static_file("/assets/{}".format(filename))
    )
    app.route(
        "/img/<filename:path>", "GET",
        lambda filename: _serve_static_file("/img/{}".format(filename))
    )
    app.route(
        "/.well-known/<filename:path>", "GET",
        lambda filename: _serve_static_file("/.well-known/{}".format(filename))
    )
    app.route(
        "/data/img/<filename:path>", "GET",
        lambda filename: bottle.static_file(
            filename,
            root=os.path.join(
                config["data_directory"],
                "images"
            )
        )
    )

    return app
