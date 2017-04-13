# coding: utf-8
"""
This module contains basic utility functions, such as pretty printing of JSON
output, checking that a value is within a given interval etc.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import datetime
import json
import logging
import math
import re

import requests
import unidecode


LOGGER = logging.getLogger(__name__)

# Constants
NAVITIA_ENDPOINT = "https://api.navitia.io/v1/coverage/fr-idf/journeys"


def pretty_json(data):
    """
    Pretty JSON output.

    :param data: The data to dump as pretty JSON.
    :return: The pretty printed JSON dump.

    :Example:

        >>> print(pretty_json({"toto": "ok", "foo": "bar"}))
        {
            "foo": "bar",
            "toto": "ok"
        }
    """
    return json.dumps(data, indent=4, separators=(',', ': '),
                      sort_keys=True)


def is_within_interval(value, min_value=None, max_value=None):
    """
    Check whether a variable is within a given interval. Assumes the value is
    always ok with respect to a `None` bound. If the `value` is `None`, it is
    always within the bounds.

    :param value: The value to check. Can be ``None``.
    :param min_value: The lower bound.
    :param max_value: The upper bound.
    :return: ``True`` if the value is ``None``. ``True`` or ``False`` whether
    the value is within the given interval or not.

    .. note:: A value is always within a ``None`` bound.

    :Example:

        >>> is_within_interval(None)
        True
        >>> is_within_interval(None, 0, 10)
        True
        >>> is_within_interval(2, None, None)
        True
        >>> is_within_interval(2, None, 3)
        True
        >>> is_within_interval(2, 1, None)
        True
        >>> is_within_interval(2, 1, 3)
        True
        >>> is_within_interval(2, 4, 7)
        False
        >>> is_within_interval(2, 4, 1)
        False
    """
    checks = []
    if value and min_value:
        checks.append(value >= min_value)
    if value and max_value:
        checks.append(value <= max_value)
    return all(checks)


def normalize_string(string):
    """
    Normalize the given string for matching.

    .. todo :: Convert romanian numerals to decimal

    :Example:

        >>> normalize_string("tétéà 14ème-XIV,  foobar")
        'tetea 14eme xiv, foobar'
    """
    # ASCIIfy the string
    string = unidecode.unidecode(string)

    # Replace any non-alphanumeric character by space
    # Keep some basic punctuation to keep syntaxic units
    string = re.sub(r"[^a-zA-Z0-9,;:]", " ", string)

    # Convert to lowercase
    string = string.lower()

    # Collapse multiple spaces, replace tabulations and newlines by space
    string = re.sub(r"\s+", " ", string)

    return string


def uniqify(some_list):
    """
    Filter out duplicates from a given list.

    :Example:

        >>> uniqify([1, 2, 2, 3])
        [1, 2, 3]
    """
    return list(set(some_list))


def distance(gps1, gps2):
    """
    Compute the distance between two tuples of latitude and longitude.

    :param gps1: First tuple of (latitude, longitude).
    :param gps2: Second tuple of (latitude, longitude).
    :return: The distance in meters.

    :Example:

        >>> int(distance([48.86786647303717, 2.19368117495212], \
                         [48.95314107920405, 2.3368043817358464]))
        14117
    """
    lat1 = math.radians(gps1[0])
    long1 = math.radians(gps1[1])

    lat2 = math.radians(gps2[0])
    long2 = math.radians(gps2[1])

    # pylint: disable=invalid-name
    a = (
        math.sin((lat2 - lat1) / 2.0)**2 +
        math.cos(lat1) * math.cos(lat2) * math.sin((long2 - long1) / 2.0)**2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    earth_radius = 6371000

    return earth_radius * c


def sort_list_of_dicts_by(flats_list, key):
    """
    Sort a list of dicts according to a given field common to all the dicts.

    :param flats_list: List of dicts to sort.
    :param key: The key of the dict items to sort on.
    :return: A sorted list.

    :Example:

        >>> sort_list_of_dicts_by([{1: 2}, {1: 1}], 1)
        [{1: 1}, {1: 2}]
    """
    return sorted(flats_list, key=lambda x: x[key])


def merge_dicts(*args):
    """
    Merge the two flats passed as argument in a single flat dict object.
    """
    if len(args) == 1:
        return args[0]
    else:
        flat1, flat2 = args[:2]
        merged_flat = {}
        for k, value2 in flat2.items():
            value1 = flat1.get(k, None)
            if value1 is None:
                # flat1 has empty matching field, just keep the flat2 field
                merged_flat[k] = value2
            elif value2 is None:
                # flat2 field is empty, just keep the flat1 field
                merged_flat[k] = value1
            else:
                # Any other case, we should merge
                # TODO: Do the merge
                merged_flat[k] = value1
        return merge_dicts(merged_flat, *args[2:])


def get_travel_time_between(latlng_from, latlng_to, config):
    """
    Query the Navitia API to get the travel time between two points identified
    by their latitude and longitude.

    :param latlng_from: A tuple of (latitude, longitude) for the starting
    point.
    :param latlng_to: A tuple of (latitude, longitude) for the destination.
    :return: The travel time in seconds. Returns ``None`` if it could not fetch
    it.

    .. note :: Uses the Navitia API. Requires a ``navitia_api_key`` field to be
    filled-in in the ``config``.
    """
    time = None

    # Check that Navitia API key is available
    if config["navitia_api_key"]:
        payload = {
            "from": "%s;%s" % (latlng_from[1], latlng_from[0]),
            "to": "%s;%s" % (latlng_to[1], latlng_to[0]),
            "datetime": datetime.datetime.now().isoformat(),
            "count": 1
        }
        try:
            # Do the query to Navitia API
            req = requests.get(
                NAVITIA_ENDPOINT, params=payload,
                auth=(config["navitia_api_key"], "")
            )
            req.raise_for_status()
            time = req.json()["journeys"][0]["durations"]["total"]
        except (requests.exceptions.RequestException,
                ValueError, IndexError, KeyError) as exc:
            # Ignore any possible exception
            LOGGER.warning(
                "An exception occurred during travel time lookup on "
                "Navitia: %s.",
                str(exc)
            )
    else:
        LOGGER.warning(
            "No API key available for travel time lookup. Please provide "
            "a Navitia API key. Skipping travel time lookup."
        )
    return time
