# coding: utf-8
"""
Main commands available for flatisfy.
"""
from __future__ import absolute_import, print_function, unicode_literals

import collections
import logging

import flatisfy.filters
from flatisfy import database
from flatisfy.models import flat as flat_model
from flatisfy import fetch
from flatisfy import tools
from flatisfy.filters import metadata
from flatisfy.web import app as web_app


LOGGER = logging.getLogger(__name__)


def filter_flats(config, flats_list, fetch_details=True):
    """
    Filter the available flats list. Then, filter it according to criteria.

    :param config: A config dict.
    :param fetch_details: Whether additional details should be fetched between
    the two passes.
    :param flats_list: The initial list of flat objects to filter.
    :return: A dict mapping flat status and list of flat objects.
    """
    # pylint: disable=locally-disabled,redefined-variable-type
    # Add the flatisfy metadata entry and prepare the flat objects
    flats_list = metadata.init(flats_list)

    first_pass_result = collections.defaultdict(list)
    second_pass_result = collections.defaultdict(list)
    # Do a first pass with the available infos to try to remove as much
    # unwanted postings as possible
    if config["passes"] > 0:
        first_pass_result = flatisfy.filters.first_pass(flats_list,
                                                        config)
    else:
        first_pass_result["new"] = flats_list

    # Load additional infos
    if fetch_details:
        for i, flat in enumerate(first_pass_result["new"]):
            details = fetch.fetch_details(config, flat["id"])
            first_pass_result["new"][i] = tools.merge_dicts(flat, details)

    # Do a second pass to consolidate all the infos we found and make use of
    # additional infos
    if config["passes"] > 1:
        second_pass_result = flatisfy.filters.second_pass(
            first_pass_result["new"], config
        )
    else:
        second_pass_result["new"] = first_pass_result["new"]

    return {
        "new": second_pass_result["new"],
        "duplicate": (
            first_pass_result["duplicate"] +
            second_pass_result["duplicate"]
        ),
        "ignored": (
            first_pass_result["ignored"] + second_pass_result["ignored"]
        )
    }


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
    flats_list_by_status = filter_flats(config, flats_list=flats_list,
                                        fetch_details=True)
    # Create database connection
    get_session = database.init_db(config["database"])

    with get_session() as session:
        for status, flats_list in flats_list_by_status.items():
            for flat_dict in flats_list:
                flat = flat_model.Flat.from_dict(flat_dict)
                flat.status = getattr(flat_model.FlatStatus, status)
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
