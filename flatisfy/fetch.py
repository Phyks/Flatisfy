# coding: utf-8
"""
This module contains all the code related to fetching and loading flats lists.
"""
from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools
import json
import logging

from flatisfy import database
from flatisfy import tools
from flatisfy.constants import BACKENDS_BY_PRECEDENCE
from flatisfy.models import flat as flat_model

LOGGER = logging.getLogger(__name__)


try:
    from weboob.capabilities.housing import Query, HOUSE_TYPES, POSTS_TYPES
    from weboob.core.bcall import CallErrors
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
            except KeyError:
                pass
        return flat

    def __init__(self, config):
        """
        Create a Weboob handle and try to load the modules.

        :param config: A config dict.
        """
        # Default backends
        if not config["backends"]:
            backends = BACKENDS_BY_PRECEDENCE
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
        cities, to comply with housing websites limitations.

        :param constraints_dict: A dictionary of constraints, as defined in the
        config.
        :return: A list of Weboob ``weboob.capabilities.housing.Query``
        objects. Returns ``None`` if an error occurred.
        """
        queries = []

        # First, find all matching cities for the postal codes in constraints
        matching_cities = []
        for postal_code in constraints_dict["postal_codes"]:
            try:
                for city in self.webnip.do("search_city", postal_code):
                    matching_cities.append(city)
            except CallErrors as exc:
                # If an error occured, just log it
                LOGGER.error(
                    (
                        "An error occured while building query for "
                        "postal code %s: %s"
                    ),
                    postal_code,
                    str(exc)
                )

                if not matching_cities:
                    # If postal code gave no match, warn the user
                    LOGGER.warn(
                        "Postal code %s could not be matched with a city.",
                        postal_code
                    )

        # Remove "TOUTES COMMUNES" entry which are duplicates of the individual
        # cities entries in Logicimmo module.
        matching_cities = [
            city
            for city in matching_cities
            if not (city.backend == 'logicimmo' and
                    city.name.startswith('TOUTES COMMUNES'))
        ]

        # Then, build queries by grouping cities by at most 3
        for cities_batch in tools.batch(matching_cities, 3):
            query = Query()
            query.cities = list(cities_batch)

            try:
                query.house_types = [
                    getattr(
                        HOUSE_TYPES,
                        house_type.upper()
                    )
                    for house_type in constraints_dict["house_types"]
                ]
            except AttributeError:
                LOGGER.error("Invalid house types constraint.")
                return None

            try:
                query.type = getattr(
                    POSTS_TYPES,
                    constraints_dict["type"].upper()
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

    def query(self, query, max_entries=None, store_personal_data=False):
        """
        Fetch the housings posts matching a given Weboob query.

        :param query: A Weboob `weboob.capabilities.housing.Query`` object.
        :param max_entries: Maximum number of entries to fetch.
        :param store_personal_data: Whether personal data should be fetched
        from housing posts (phone number etc).
        :return: The matching housing posts, dumped as a list of JSON objects.
        """
        housings = []
        # TODO: Handle max_entries better
        try:
            for housing in itertools.islice(
                    self.webnip.do('search_housings', query),
                    max_entries
            ):
                if not store_personal_data:
                    housing.phone = None
                housings.append(json.dumps(housing, cls=WeboobEncoder))
        except CallErrors as exc:
            # If an error occured, just log it
            LOGGER.error(
                "An error occured while fetching the housing posts: %s",
                str(exc)
            )
        return housings

    def info(self, full_flat_id, store_personal_data=False):
        """
        Get information (details) about an housing post.

        :param full_flat_id: A Weboob housing post id, in complete form
        (ID@BACKEND)
        :param store_personal_data: Whether personal data should be fetched
        from housing posts (phone number etc).
        :return: The details in JSON.
        """
        flat_id, backend_name = full_flat_id.rsplit("@", 1)
        try:
            backend = next(
                backend
                for backend in self.backends
                if backend.name == backend_name
            )
        except StopIteration:
            LOGGER.error("Backend %s is not available.", backend_name)
            return "{}"

        try:
            housing = backend.get_housing(flat_id)
            fields = [x[0] for x in housing.iter_fields()]
            # TODO: Only laod phone in the end, after filtering
            if not store_personal_data:
                # Avoid making unwanted requests
                fields = [x for x in fields if x != "phone"]
            housing = backend.fillobj(housing, fields=fields)
            # Otherwise, we miss the @backend afterwards
            housing.id = full_flat_id
            if not store_personal_data:
                # Ensure personal data is cleared
                housing.phone = None

            return json.dumps(housing, cls=WeboobEncoder)
        except Exception as exc:  # pylint: disable=broad-except
            # If an error occured, just log it
            LOGGER.error(
                "An error occured while fetching housing %s: %s",
                full_flat_id,
                str(exc)
            )
            return "{}"


def fetch_flats(config):
    """
    Fetch the available flats using the Flatboob / Weboob config.

    :param config: A config dict.
    :return: A dict mapping constraint in config to all available matching
    flats.
    """
    fetched_flats = {}

    for constraint_name, constraint in config["constraints"].items():
        LOGGER.info("Loading flats for constraint %s...", constraint_name)
        with WeboobProxy(config) as weboob_proxy:
            queries = weboob_proxy.build_queries(constraint)
            housing_posts = []
            for query in queries:
                housing_posts.extend(
                    weboob_proxy.query(query, config["max_entries"],
                                       config["store_personal_data"])
                )
        LOGGER.info("Fetched %d flats.", len(housing_posts))

        constraint_flats_list = [json.loads(flat) for flat in housing_posts]
        constraint_flats_list = [WeboobProxy.restore_decimal_fields(flat)
                                 for flat in constraint_flats_list]
        fetched_flats[constraint_name] = constraint_flats_list
    return fetched_flats


def fetch_details(config, flat_id):
    """
    Fetch the additional details for a flat using Flatboob / Weboob.

    :param config: A config dict.
    :param flat_id: ID of the flat to fetch details for.
    :return: A flat dict with all the available data.
    """
    with WeboobProxy(config) as weboob_proxy:
        LOGGER.info("Loading additional details for flat %s.", flat_id)
        weboob_output = weboob_proxy.info(flat_id,
                                          config["store_personal_data"])

    flat_details = json.loads(weboob_output)
    flat_details = WeboobProxy.restore_decimal_fields(flat_details)
    LOGGER.info("Fetched details for flat %s.", flat_id)

    return flat_details


def load_flats_from_file(json_file, config):
    """
    Load a dumped flats list from JSON file.

    :param json_file: The file to load housings list from.
    :return: A dict mapping constraint in config to all available matching
    flats.

    .. note::
        As we do not know which constraint is met by a given flat, all the
        flats are returned for any available constraint, and they will be
        filtered out afterwards.
    """
    flats_list = []
    try:
        LOGGER.info("Loading flats list from file %s", json_file)
        with open(json_file, "r") as fh:
            flats_list = json.load(fh)
        LOGGER.info("Found %d flats.", len(flats_list))
    except (IOError, ValueError):
        LOGGER.error("File %s is not a valid dump file.", json_file)
    return {
        constraint_name: flats_list
        for constraint_name in config["constraints"]
    }


def load_flats_from_db(config):
    """
    Load flats from database.

    :param config: A config dict.
    :return: A dict mapping constraint in config to all available matching
    flats.
    """
    get_session = database.init_db(config["database"], config["search_index"])

    loaded_flats = collections.defaultdict(list)
    with get_session() as session:
        for flat in session.query(flat_model.Flat).all():
            loaded_flats[flat.flatisfy_constraint].append(flat.json_api_repr())
    return loaded_flats
