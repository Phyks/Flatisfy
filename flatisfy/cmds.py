# coding: utf-8
"""
Main commands available for flatisfy.
"""
from __future__ import absolute_import, print_function, unicode_literals

import collections
import logging
import os

import flatisfy.filters
from flatisfy import database
from flatisfy import email
from flatisfy.models import flat as flat_model
from flatisfy.models import postal_code as postal_code_model
from flatisfy.models import public_transport as public_transport_model
from flatisfy import fetch
from flatisfy import tools
from flatisfy.filters import metadata
from flatisfy.web import app as web_app
import time

LOGGER = logging.getLogger(__name__)


def filter_flats_list(
    config, constraint_name, flats_list, fetch_details=True, past_flats=None
):
    """
    Filter the available flats list. Then, filter it according to criteria.

    :param config: A config dict.
    :param constraint_name: The constraint name that the ``flats_list`` should
        satisfy.
    :param flats_list: The initial list of flat objects to filter.
    :param fetch_details: Whether additional details should be fetched between
        the two passes.
    :param past_flats: The list of already fetched flats
    :return: A dict mapping flat status and list of flat objects.
    """
    # Add the flatisfy metadata entry and prepare the flat objects
    flats_list = metadata.init(flats_list, constraint_name)

    # Get the associated constraint from config
    try:
        constraint = config["constraints"][constraint_name]
    except KeyError:
        LOGGER.error(
            "Missing constraint %s. Skipping filtering for these posts.",
            constraint_name,
        )
        return {"new": [], "duplicate": [], "ignored": []}

    first_pass_result = collections.defaultdict(list)
    second_pass_result = collections.defaultdict(list)
    third_pass_result = collections.defaultdict(list)
    # Do a first pass with the available infos to try to remove as much
    # unwanted postings as possible
    if config["passes"] > 0:
        first_pass_result = flatisfy.filters.first_pass(flats_list, constraint, config)
    else:
        first_pass_result["new"] = flats_list

    # Load additional infos
    if fetch_details:
        past_ids = {x["id"]: x for x in past_flats} if past_flats else {}
        for i, flat in enumerate(first_pass_result["new"]):
            details = None

            use_cache = past_ids.get(flat["id"])
            if use_cache:
                LOGGER.info("Skipping details download for %s.", flat["id"])
                details = use_cache
            else:
                details = fetch.fetch_details(config, flat["id"])
                if flat["id"].endswith("@leboncoin"):
                    # sleep 0.5s to avoid rate-kick
                    time.sleep(0.5)

            first_pass_result["new"][i] = tools.merge_dicts(flat, details)

    # Do a second pass to consolidate all the infos we found and make use of
    # additional infos
    if config["passes"] > 1:
        second_pass_result = flatisfy.filters.second_pass(
            first_pass_result["new"], constraint, config
        )
    else:
        second_pass_result["new"] = first_pass_result["new"]

    # Do a third pass to deduplicate better
    if config["passes"] > 2:
        third_pass_result = flatisfy.filters.third_pass(
            second_pass_result["new"], config
        )
    else:
        third_pass_result["new"] = second_pass_result["new"]

    return {
        "new": third_pass_result["new"],
        "duplicate": (
            first_pass_result["duplicate"]
            + second_pass_result["duplicate"]
            + third_pass_result["duplicate"]
        ),
        "ignored": (
            first_pass_result["ignored"]
            + second_pass_result["ignored"]
            + third_pass_result["ignored"]
        ),
    }


def filter_fetched_flats(config, fetched_flats, fetch_details=True, past_flats={}):
    """
    Filter the available flats list. Then, filter it according to criteria.

    :param config: A config dict.
    :param fetch_details: Whether additional details should be fetched between
        the two passes.
    :param fetched_flats: The initial dict mapping constraints to the list of
        fetched flat objects to filter.
    :return: A dict mapping constraints to a dict mapping flat status and list
        of flat objects.
    """
    for constraint_name, flats_list in fetched_flats.items():
        fetched_flats[constraint_name] = filter_flats_list(
            config,
            constraint_name,
            flats_list,
            fetch_details,
            past_flats.get(constraint_name, None),
        )
    return fetched_flats


def import_and_filter(config, load_from_db=False, new_only=False):
    """
    Fetch the available flats list. Then, filter it according to criteria.
    Finally, store it in the database.

    :param config: A config dict.
    :param load_from_db: Whether to load flats from database or fetch them
        using WebOOB.
    :return: ``None``.
    """
    # Fetch and filter flats list
    past_flats = fetch.load_flats_from_db(config)
    if load_from_db:
        fetched_flats = past_flats
    else:
        fetched_flats = fetch.fetch_flats(config)
    # Do not fetch additional details if we loaded data from the db.
    flats_by_status = filter_fetched_flats(
        config,
        fetched_flats=fetched_flats,
        fetch_details=(not load_from_db),
        past_flats=past_flats if new_only else {},
    )
    # Create database connection
    get_session = database.init_db(config["database"], config["search_index"])

    new_flats = []

    LOGGER.info("Merging fetched flats in database...")
    # Flatten the flats_by_status dict
    flatten_flats_by_status = collections.defaultdict(list)
    for flats in flats_by_status.values():
        for status, flats_list in flats.items():
            flatten_flats_by_status[status].extend(flats_list)

    with get_session() as session:
        # Set is_expired to true for all existing flats.
        # This will be set back to false if we find them during importing.
        for flat in session.query(flat_model.Flat).all():
            flat.is_expired = True

        for status, flats_list in flatten_flats_by_status.items():
            # Build SQLAlchemy Flat model objects for every available flat
            flats_objects = {
                flat_dict["id"]: flat_model.Flat.from_dict(flat_dict)
                for flat_dict in flats_list
            }

            if flats_objects:
                # If there are some flats, try to merge them with the ones in
                # db
                existing_flats_queries = session.query(flat_model.Flat).filter(
                    flat_model.Flat.id.in_(flats_objects.keys())
                )
                for each in existing_flats_queries.all():
                    # For each flat to merge, take care not to overwrite the
                    # status if the user defined it
                    flat_object = flats_objects[each.id]
                    if each.status in flat_model.AUTOMATED_STATUSES:
                        flat_object.status = getattr(flat_model.FlatStatus, status)
                    else:
                        flat_object.status = each.status

                    # Every flat we fetched isn't expired
                    flat_object.is_expired = False

                    # For each flat already in the db, merge it (UPDATE)
                    # instead of adding it
                    session.merge(flats_objects.pop(each.id))

            # For any other flat, it is not already in the database, so we can
            # just set the status field without worrying
            for flat in flats_objects.values():
                flat.status = getattr(flat_model.FlatStatus, status)
                if flat.status == flat_model.FlatStatus.new:
                    new_flats.append(flat)

            session.add_all(flats_objects.values())

        if config["send_email"]:
            email.send_notification(config, new_flats)

    LOGGER.info(f"Found {len(new_flats)} new flats.")

    # Touch a file to indicate last update timestamp
    ts_file = os.path.join(config["data_directory"], "timestamp")
    with open(ts_file, "w"):
        os.utime(ts_file, None)

    LOGGER.info("Done!")


def purge_db(config):
    """
    Purge the database.

    :param config: A config dict.
    :return: ``None``
    """
    get_session = database.init_db(config["database"], config["search_index"])

    with get_session() as session:
        # Delete every flat in the db
        LOGGER.info("Purge all flats from the database.")
        for flat in session.query(flat_model.Flat).all():
            # Use (slower) deletion by object, to ensure whoosh index is
            # updated
            session.delete(flat)
        LOGGER.info("Purge all postal codes from the database.")
        session.query(postal_code_model.PostalCode).delete()
        LOGGER.info("Purge all public transportations from the database.")
        session.query(public_transport_model.PublicTransport).delete()


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

    print(
        "Launching web viewer running on http://%s:%s"
        % (config["host"], config["port"])
    )
    app.run(host=config["host"], port=config["port"], server=server)
