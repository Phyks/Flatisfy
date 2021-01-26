# coding: utf-8
"""
Expose a WSGI-compatible application to serve with a webserver.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
import sys

import flatisfy.config
from flatisfy.web import app as web_app


class Args:
    config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/config.json")


LOGGER = logging.getLogger("flatisfy")


CONFIG = flatisfy.config.load_config(Args())
if CONFIG is None:
    LOGGER.error("Invalid configuration. Exiting. Run init-config before if this is the first time you run Flatisfy.")
    sys.exit(1)


application = app = web_app.get_app(CONFIG)
