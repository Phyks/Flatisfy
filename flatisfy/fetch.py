# coding: utf-8
"""
This module contains all the code related to fetching and loading flats lists.
"""
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging
import subprocess


LOGGER = logging.getLogger(__name__)


def fetch_flats_list(config):
    """
    Fetch the available flats using the Flatboob / Weboob config.

    :param config: A config dict.
    :return: A list of all available flats.
    """
    flats_list = []
    for query in config["queries"]:
        max_entries = config["max_entries"]
        if max_entries is None:
            max_entries = 0

        LOGGER.info("Loading flats from query %s.", query)
        flatboob_output = subprocess.check_output(
            ["../weboob/tools/local_run.sh", "../weboob/scripts/flatboob",
             "-n", str(max_entries), "-f", "json", "load", query]
        )
        query_flats_list = json.loads(flatboob_output)
        LOGGER.info("Fetched %d flats.", len(query_flats_list))
        flats_list.extend(query_flats_list)
    LOGGER.info("Fetched a total of %d flats.", len(flats_list))
    return flats_list


def fetch_details(flat_id):
    """
    Fetch the additional details for a flat using Flatboob / Weboob.

    :param flat_id: ID of the flat to fetch details for.
    :return: A flat dict with all the available data.
    """
    LOGGER.info("Loading additional details for flat %s.", flat_id)
    flatboob_output = subprocess.check_output(
        ["../weboob/tools/local_run.sh", "../weboob/scripts/flatboob",
         "-f", "json", "info", flat_id]
    )
    flat_details = json.loads(flatboob_output)
    LOGGER.info("Fetched details for flat %s.", flat_id)

    if flat_details:
        flat_details = flat_details[0]

    return flat_details


def load_flats_list(json_file):
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
