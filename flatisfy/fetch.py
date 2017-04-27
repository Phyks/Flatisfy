# coding: utf-8
"""
This module contains all the code related to fetching and loading flats lists.
"""
from __future__ import absolute_import, print_function, unicode_literals

import itertools
import json
import logging

from flatisfy import database
from flatisfy import tools
from flatisfy.models import flat as flat_model

LOGGER = logging.getLogger(__name__)


try:
    from weboob.capabilities.housing import Query
    from weboob.core.ouiboube import WebNip
    from weboob.tools.json import WeboobEncoder
except ImportError:
    LOGGER.error("Weboob is not available on your system. Make sure you "
                 "installed it.")
    raise


class WeboobProxy(object):
    """
    Wrapper around Weboob ``WebNip`` class, to fetch housing posts without
    having to spawn a subprocess.
    """
    @staticmethod
    def version():
        """
        Get Weboob version.

        :return: The installed Weboob version.
        """
        return WebNip.VERSION

    @staticmethod
    def restore_decimal_fields(flat):
        """
        Parse fields expected to be in Decimal type to float. They were dumped
        as str in the JSON dump process.

        :param flat: A flat dict.
        :return: A flat dict with Decimal fields converted to float.
        """
        for field in ["area", "cost", "rooms", "bedrooms", "price_per_meter"]:
            try:
                flat[field] = float(flat[field])
            except (TypeError, ValueError):
                flat[field] = None
        return flat

    def __init__(self, config):
        """
        Create a Weboob handle and try to load the modules.

        :param config: A config dict.
        """
        # Default backends
        if not config["backends"]:
            backends = ["seloger", "pap", "leboncoin", "logicimmo",
                        "explorimmo", "entreparticuliers"]
        else:
            backends = config["backends"]

        # Create base WebNip object
        self.webnip = WebNip(modules_path=config["modules_path"])

        # Create backends
        self.backends = [
            self.webnip.load_backend(
                module,
                module,
                params={}
            )
            for module in backends
        ]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.webnip.deinit()

    def build_queries(self, constraints_dict):
        """
        Build Weboob ``weboob.capabilities.housing.Query`` objects from the
        constraints defined in the configuration. Each query has at most 3
        postal codes, to comply with housing websites limitations.

        :param constraints_dict: A dictionary of constraints, as defined in the
        config.
        :return: A list of Weboob ``weboob.capabilities.housing.Query``
        objects. Returns ``None`` if an error occurred.
        """
        queries = []
        for postal_codes in tools.batch(constraints_dict["postal_codes"], 3):
            query = Query()
            query.cities = []
            for postal_code in postal_codes:
                try:
                    for city in self.webnip.do("search_city", postal_code):
                        query.cities.append(city)
                except IndexError:
                    LOGGER.error(
                        "Postal code %s could not be matched with a city.",
                        postal_code
                    )
                    return None

            try:
                query.house_types = [
                    getattr(
                        Query.HOUSE_TYPES,
                        house_type.upper()
                    )
                    for house_type in constraints_dict["house_types"]
                ]
            except AttributeError:
                LOGGER.error("Invalid house types constraint.")
                return None

            try:
                query.type = getattr(
                    Query,
                    "TYPE_{}".format(constraints_dict["type"].upper())
                )
            except AttributeError:
                LOGGER.error("Invalid post type constraint.")
                return None

            query.area_min = constraints_dict["area"][0]
            query.area_max = constraints_dict["area"][1]
            query.cost_min = constraints_dict["cost"][0]
            query.cost_max = constraints_dict["cost"][1]
            query.nb_rooms = constraints_dict["rooms"][0]

            queries.append(query)

        return queries

    def query(self, query, max_entries=None):
        """
        Fetch the housings posts matching a given Weboob query.

        :param query: A Weboob `weboob.capabilities.housing.Query`` object.
        :param max_entries: Maximum number of entries to fetch.
        :return: The matching housing posts, dumped as a list of JSON objects.
        """
        housings = []
        # TODO: Handle max_entries better
        for housing in itertools.islice(
                self.webnip.do('search_housings', query),
                max_entries
        ):
            housings.append(json.dumps(housing, cls=WeboobEncoder))
        return housings

    def info(self, full_flat_id):
        """
        Get information (details) about an housing post.

        :param full_flat_id: A Weboob housing post id, in complete form
        (ID@BACKEND)
        :return: The details in JSON.
        """
        flat_id, backend_name = full_flat_id.rsplit("@", 1)
        backend = next(
            backend
            for backend in self.backends
            if backend.name == backend_name
        )
        housing = backend.get_housing(flat_id)
        housing.id = full_flat_id  # Otherwise, we miss the @backend afterwards
        return json.dumps(housing, cls=WeboobEncoder)


def fetch_flats_list(config):
    """
    Fetch the available flats using the Flatboob / Weboob config.

    :param config: A config dict.
    :return: A list of all available flats.
    """
    flats_list = []

    with WeboobProxy(config) as weboob_proxy:
        LOGGER.info("Loading flats...")
        queries = weboob_proxy.build_queries(config["constraints"])
        housing_posts = []
        for query in queries:
            housing_posts.extend(
                weboob_proxy.query(query, config["max_entries"])
            )
        LOGGER.info("Fetched %d flats.", len(housing_posts))

    flats_list = [json.loads(flat) for flat in housing_posts]
    flats_list = [WeboobProxy.restore_decimal_fields(flat)
                  for flat in flats_list]
    return flats_list


def fetch_details(config, flat_id):
    """
    Fetch the additional details for a flat using Flatboob / Weboob.

    :param config: A config dict.
    :param flat_id: ID of the flat to fetch details for.
    :return: A flat dict with all the available data.
    """
    with WeboobProxy(config) as weboob_proxy:
        LOGGER.info("Loading additional details for flat %s.", flat_id)
        weboob_output = weboob_proxy.info(flat_id)

    flat_details = json.loads(weboob_output)
    flat_details = WeboobProxy.restore_decimal_fields(flat_details)
    LOGGER.info("Fetched details for flat %s.", flat_id)

    return flat_details


def load_flats_list_from_file(json_file):
    """
    Load a dumped flats list from JSON file.

    :param json_file: The file to load housings list from.
    :return: A list of all the flats in the dump file.
    """
    flats_list = []
    try:
        LOGGER.info("Loading flats list from file %s", json_file)
        with open(json_file, "r") as fh:
            flats_list = json.load(fh)
        LOGGER.info("Found %d flats.", len(flats_list))
    except (IOError, ValueError):
        LOGGER.error("File %s is not a valid dump file.", json_file)
    return flats_list


def load_flats_list_from_db(config):
    """
    Load flats from database.

    :param config: A config dict.
    :return: A list of all the flats in the database.
    """
    flats_list = []
    get_session = database.init_db(config["database"])

    with get_session() as session:
        # TODO: Better serialization
        flats_list = [flat.json_api_repr()
                      for flat in session.query(flat_model.Flat).all()]
    return flats_list
