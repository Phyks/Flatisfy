# coding: utf-8
"""
Main commands available for flatisfy.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging

import flatisfy.filters
from flatisfy import database
from flatisfy.models import flat as flat_model
from flatisfy import fetch
from flatisfy import tools
from flatisfy.web import app as web_app


LOGGER = logging.getLogger(__name__)


def filter_flats(config, flats_list=None, fetch_details=True):
    """
    Filter the available flats list. Then, filter it according to criteria.

    :param config: A config dict.
    :param fetch_details: Whether additional details should be fetched between
    the two passes.
    :param flats_list: The initial list of flat objects to filter.
    :return: A tuple of the list of all matching flats and the list of ignored
    flats.
    """
    # Do a first pass with the available infos to try to remove as much
    # unwanted postings as possible
    if config["passes"] > 0:
        flats_list, ignored_flats = flatisfy.filters.first_pass(flats_list,
                                                                config)

    # Do a second pass to consolidate all the infos we found and make use of
    # additional infos
    if config["passes"] > 1:
        # Load additional infos
        if fetch_details:
            for i, flat in enumerate(flats_list):
                details = fetch.fetch_details(config, flat["id"])
                flats_list[i] = tools.merge_dicts(flat, details)

        flats_list, extra_ignored_flats = flatisfy.filters.second_pass(
            flats_list, config
        )
        ignored_flats.extend(extra_ignored_flats)

    return flats_list, ignored_flats


def import_and_filter(config, load_from_db=False):
    """
    Fetch the available flats list. Then, filter it according to criteria.
    Finally, store it in the database.

    :param config: A config dict.
    :param load_from_db: Whether to load flats from database or fetch them
    using Weboob.
    :return: ``None``.
    """
    # Fetch and filter flats list
    if load_from_db:
        flats_list = fetch.load_flats_list_from_db(config)
    else:
        flats_list = fetch.fetch_flats_list(config)
    flats_list, ignored_list = filter_flats(config, flats_list=flats_list,
                                            fetch_details=True)
    # Create database connection
    get_session = database.init_db(config["database"])

    with get_session() as session:
        for flat_dict in flats_list:
            flat = flat_model.Flat.from_dict(flat_dict)
            session.merge(flat)

        for flat_dict in ignored_list:
            flat = flat_model.Flat.from_dict(flat_dict)
            flat.status = flat_model.FlatStatus.ignored
            session.merge(flat)


def purge_db(config):
    """
    Purge the database.

    :param config: A config dict.
    :return: ``None``
    """
    get_session = database.init_db(config["database"])

    with get_session() as session:
        # Delete every flat in the db
        LOGGER.info("Purge all flats from the database.")
        session.query(flat_model.Flat).delete(synchronize_session=False)


def serve(config):
    """
    Serve the web app.

    :param config: A config dict.
    :return: ``None``, long-running process.
    """
    app = web_app.get_app(config)

    server = config.get("webserver", None)
    if not server:
        # Default webserver is quiet, as Bottle is used with Canister for
        # standard logging
        server = web_app.QuietWSGIRefServer

    app.run(host=config["host"], port=config["port"], server=server)
