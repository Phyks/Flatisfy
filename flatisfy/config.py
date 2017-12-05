# coding: utf-8
"""
This module handles the configuration management for Flatisfy.

It loads the default configuration, then overloads it with the provided config
file and then overloads it with command-line options.
"""
from __future__ import absolute_import, print_function, unicode_literals
from builtins import str

import json
import logging
import os
import sys
import traceback

import appdirs

from flatisfy import data
from flatisfy import tools
from flatisfy.models.postal_code import PostalCode


# Default configuration
DEFAULT_CONFIG = {
    # Constraints to match
    "constraints": {
        "default": {
            "type": None,  # RENT, SALE, SHARING
            "house_types": [],  # List of house types, must be in APART, HOUSE,
                                # PARKING, LAND, OTHER or UNKNOWN
            "postal_codes": [],  # List of postal codes
            "area": (None, None),  # (min, max) in m^2
            "cost": (None, None),  # (min, max) in currency unit
            "rooms": (None, None),  # (min, max)
            "bedrooms": (None, None),  # (min, max)
            "minimum_nb_photos": None,  # min number of photos
            "description_should_contain": [],  # list of terms
            "time_to": {}  # Dict mapping names to {"gps": [lat, lng],
                           #                        "time": (min, max) }
                           # Time is in seconds
        }
    },
    # Whether or not to store personal data from housing posts (phone number
    # etc)
    "store_personal_data": False,
    # Navitia API key
    "navitia_api_key": None,
    # Number of filtering passes to run
    "passes": 3,
    # Maximum number of entries to fetch
    "max_entries": None,
    # Directory in wich data will be put. ``None`` is XDG default location.
    "data_directory": None,
    # Path to the modules directory containing all Weboob modules. ``None`` if
    # ``weboob_modules`` package is pip-installed, and you want to use
    # ``pkgresource`` to automatically find it.
    "modules_path": None,
    # SQLAlchemy URI to the database to use
    "database": None,
    # Path to the Whoosh search index file. Use ``None`` to put it in
    # ``data_directory``.
    "search_index": None,
    # Web app port
    "port": 8080,
    # Debug mode for webserver
    "debug": False,
    # Web app host to listen on
    "host": "127.0.0.1",
    # Web server to use to serve the webapp (see Bottle deployment doc)
    "webserver": None,
    # List of Weboob backends to use (default to any backend available)
    "backends": None,
    # Should email notifications be sent?
    "send_email": False,
    "smtp_server": 'localhost',
    "smtp_port": 25,
    "smtp_from": "noreply@flatisfy.org",
    "smtp_to": [],
    # The web site url, to be used in email notifications. (doesn't matter
    # whether the trailing slash is present or not)
    "website_url": "http://127.0.0.1:8080"
}

LOGGER = logging.getLogger(__name__)


def validate_config(config, check_with_data):
    """
    Check that the config passed as argument is a valid configuration.

    :param config: A config dictionary to fetch.
    :param check_with_data: Whether we should use the available OpenData to
        check the config values.
    :return: ``True`` if the configuration is valid, ``False`` otherwise.
    """
    def _check_constraints_bounds(bounds):
        """
        Check the bounds for numeric constraints.
        """
        assert isinstance(bounds, list)
        assert len(bounds) == 2
        assert all(
            x is None or
            (
                isinstance(x, (float, int)) and
                x >= 0
            )
            for x in bounds
        )
        if bounds[0] is not None and bounds[1] is not None:
            assert bounds[1] > bounds[0]

    try:
        # Note: The traceback fetching code only handle single line asserts.
        # Then, we disable line-too-long pylint check and E501 flake8 checks
        # and use long lines whenever needed, in order to have the full assert
        # message in the log output.
        # pylint: disable=locally-disabled,line-too-long

        assert config["passes"] in [0, 1, 2, 3]
        assert config["max_entries"] is None or (isinstance(config["max_entries"], int) and config["max_entries"] > 0)  # noqa: E501

        assert config["data_directory"] is None or isinstance(config["data_directory"], str)  # noqa: E501
        assert os.path.isdir(config["data_directory"])
        assert isinstance(config["search_index"], str)
        assert config["modules_path"] is None or isinstance(config["modules_path"], str)  # noqa: E501

        assert config["database"] is None or isinstance(config["database"], str)  # noqa: E501

        assert isinstance(config["debug"], bool)
        assert isinstance(config["port"], int)
        assert isinstance(config["host"], str)
        assert config["webserver"] is None or isinstance(config["webserver"], str)  # noqa: E501
        assert config["backends"] is None or isinstance(config["backends"], list)  # noqa: E501

        assert isinstance(config["send_email"], bool)
        assert config["smtp_server"] is None or isinstance(config["smtp_server"], str)  # noqa: E501
        assert config["smtp_port"] is None or isinstance(config["smtp_port"], int)  # noqa: E501
        assert config["smtp_to"] is None or isinstance(config["smtp_to"], list)

        assert isinstance(config["store_personal_data"], bool)

        # Ensure constraints are ok
        assert config["constraints"]
        for constraint in config["constraints"].values():
            assert "type" in constraint
            assert isinstance(constraint["type"], str)
            assert constraint["type"].upper() in ["RENT", "SALE", "SHARING"]

            assert "minimum_nb_photos" in constraint
            if constraint["minimum_nb_photos"]:
                assert isinstance(constraint["minimum_nb_photos"], int)
                assert constraint["minimum_nb_photos"] >= 0

            assert "description_should_contain" in constraint
            assert isinstance(constraint["description_should_contain"], list)
            if constraint["description_should_contain"]:
                for term in constraint["description_should_contain"]:
                    assert isinstance(term, str)

            assert "house_types" in constraint
            assert constraint["house_types"]
            for house_type in constraint["house_types"]:
                assert house_type.upper() in ["APART", "HOUSE", "PARKING", "LAND", "OTHER", "UNKNOWN"]  # noqa: E501

            assert "postal_codes" in constraint
            assert constraint["postal_codes"]
            assert all(isinstance(x, str) for x in constraint["postal_codes"])
            if check_with_data:
                opendata_postal_codes = [
                    x.postal_code
                    for x in data.load_data(PostalCode, constraint, config)
                ]
                for postal_code in constraint["postal_codes"]:
                    assert postal_code in opendata_postal_codes  # noqa: E501

            assert "area" in constraint
            _check_constraints_bounds(constraint["area"])

            assert "cost" in constraint
            _check_constraints_bounds(constraint["cost"])

            assert "rooms" in constraint
            _check_constraints_bounds(constraint["rooms"])

            assert "bedrooms" in constraint
            _check_constraints_bounds(constraint["bedrooms"])

            assert "time_to" in constraint
            assert isinstance(constraint["time_to"], dict)
            for name, item in constraint["time_to"].items():
                assert isinstance(name, str)
                assert "gps" in item
                assert isinstance(item["gps"], list)
                assert len(item["gps"]) == 2
                assert "time" in item
                _check_constraints_bounds(item["time"])

        return True
    except (AssertionError, KeyError):
        _, _, exc_traceback = sys.exc_info()
        return traceback.extract_tb(exc_traceback)[-1][-1]


def load_config(args=None, check_with_data=True):
    """
    Load the configuration from file.

    :param args: An argparse args structure.
    :param check_with_data: Whether we should use the available OpenData to
        check the config values. Defaults to ``True``.
    :return: The loaded config dict.
    """
    LOGGER.info("Initializing configuration...")
    # Default configuration
    config_data = DEFAULT_CONFIG.copy()

    # Load config from specified JSON
    if args and getattr(args, "config", None):
        LOGGER.debug("Loading configuration from %s.", args.config)
        try:
            with open(args.config, "r") as fh:
                config_data.update(json.load(fh))
        except (IOError, ValueError) as exc:
            LOGGER.error(
                "Unable to load configuration from file, "
                "using default configuration: %s.",
                exc
            )

    # Overload config with arguments
    if args and getattr(args, "passes", None) is not None:
        LOGGER.debug(
            "Overloading number of passes from CLI arguments: %d.",
            args.passes
        )
        config_data["passes"] = args.passes
    if args and getattr(args, "max_entries", None) is not None:
        LOGGER.debug(
            "Overloading maximum number of entries from CLI arguments: %d.",
            args.max_entries
        )
        config_data["max_entries"] = args.max_entries
    if args and getattr(args, "port", None) is not None:
        LOGGER.debug("Overloading web app port: %d.", args.port)
        config_data["port"] = args.port
    if args and getattr(args, "host", None) is not None:
        LOGGER.debug("Overloading web app host: %s.", args.host)
        config_data["host"] = str(args.host)

    # Handle data_directory option
    if args and getattr(args, "data_dir", None) is not None:
        LOGGER.debug("Overloading data directory from CLI arguments.")
        config_data["data_directory"] = args.data_dir
    elif config_data["data_directory"] is None:
        config_data["data_directory"] = appdirs.user_data_dir(
            "flatisfy",
            "flatisfy"
        )
        LOGGER.debug("Using default XDG data directory: %s.",
                     config_data["data_directory"])

    if not os.path.isdir(config_data["data_directory"]):
        LOGGER.info("Creating data directory according to config: %s",
                    config_data["data_directory"])
        os.mkdir(config_data["data_directory"])

    if config_data["database"] is None:
        config_data["database"] = "sqlite:///" + os.path.join(
            config_data["data_directory"],
            "flatisfy.db"
        )

    if config_data["search_index"] is None:
        config_data["search_index"] = os.path.join(
            config_data["data_directory"],
            "search_index"
        )

    # Handle constraints filtering
    if args and getattr(args, "constraints", None) is not None:
        LOGGER.info(
            ("Filtering constraints from config according to CLI argument. "
             "Using only the following constraints: %s."),
            args.constraints.replace(",", ", ")
        )
        constraints_filter = args.constraints.split(",")
        config_data["constraints"] = {
            k: v
            for k, v in config_data["constraints"].items()
            if k in constraints_filter
        }

    # Sanitize website url
    if config_data["website_url"] is not None:
        if config_data["website_url"][-1] != '/':
            config_data["website_url"] += '/'

    config_validation = validate_config(config_data, check_with_data)
    if config_validation is True:
        LOGGER.info("Config has been fully initialized.")
        return config_data
    LOGGER.error("Error in configuration: %s.", config_validation)
    return None


def init_config(output=None):
    """
    Initialize an empty configuration file.

    :param output: File to output content to. Defaults to ``stdin``.
    """
    config_data = DEFAULT_CONFIG.copy()

    if output and output != "-":
        with open(output, "w") as fh:
            fh.write(tools.pretty_json(config_data))
    else:
        print(tools.pretty_json(config_data))
