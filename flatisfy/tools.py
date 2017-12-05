# coding: utf-8
"""
This module contains basic utility functions, such as pretty printing of JSON
output, checking that a value is within a given interval etc.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import datetime
import itertools
import json
import logging
import math
import re
import time

import requests
import unidecode


LOGGER = logging.getLogger(__name__)

# Constants
NAVITIA_ENDPOINT = "https://api.navitia.io/v1/coverage/fr-idf/journeys"


def hash_dict(func):
    """
    Decorator to use on functions accepting dict parameters, to transform them
    into immutable dicts and be able to use lru_cache.

    From https://stackoverflow.com/a/44776960.
    """
    class HDict(dict):
        """
        Transform mutable dictionnary into immutable. Useful to be compatible
        with lru_cache
        """
        def __hash__(self):
            return hash(json.dumps(self))

    def wrapped(*args, **kwargs):
        """
        The wrapped function
        """
        args = tuple(
            [
                HDict(arg) if isinstance(arg, dict) else arg
                for arg in args
            ]
        )
        kwargs = {
            k: HDict(v) if isinstance(v, dict) else v
            for k, v in kwargs.items()
        }
        return func(*args, **kwargs)
    return wrapped


class DateAwareJSONEncoder(json.JSONEncoder):
    """
    Extend the default JSON encoder to serialize datetimes to iso strings.
    """
    def default(self, o):  # pylint: disable=locally-disabled,E0202
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


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
    return json.dumps(data, cls=DateAwareJSONEncoder,
                      indent=4, separators=(',', ': '),
                      sort_keys=True)


def batch(iterable, size):
    """
    Get items from a sequence a batch at a time.

    :param iterable: The iterable to get the items from.
    :param size: The size of the batches.
    :return: A new iterable.
    """
    sourceiter = iter(iterable)
    while True:
        batchiter = itertools.islice(sourceiter, size)
        yield itertools.chain([next(batchiter)], batchiter)


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

    .. note::

        A value is always within a ``None`` bound.

    Example::

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

    :Example:

        >>> normalize_string("tétéà 14ème-XIV,  foobar")
        'tetea 14eme xiv, foobar'
    """
    # TODO: Convert romanian numerals to decimal
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

    # pylint: disable=locally-disabled,invalid-name
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

    flat1, flat2 = args[:2]  # pylint: disable=locally-disabled,unbalanced-tuple-unpacking,line-too-long
    merged_flat = {}
    for k, value2 in flat2.items():
        value1 = flat1.get(k, None)

        if k in ["urls", "merged_ids"]:
            # Handle special fields separately
            merged_flat[k] = list(set(value2 + value1))
            continue

        if not value1:
            # flat1 has empty matching field, just keep the flat2 field
            merged_flat[k] = value2
        elif not value2:
            # flat2 field is empty, just keep the flat1 field
            merged_flat[k] = value1
        else:
            # Any other case, we should keep the value of the more recent flat
            # dict (the one most at right in arguments)
            merged_flat[k] = value2
    for k in [key for key in flat1.keys() if key not in flat2.keys()]:
        merged_flat[k] = flat1[k]
    return merge_dicts(merged_flat, *args[2:])


def get_travel_time_between(latlng_from, latlng_to, config):
    """
    Query the Navitia API to get the travel time between two points identified
    by their latitude and longitude.

    :param latlng_from: A tuple of (latitude, longitude) for the starting
        point.
    :param latlng_to: A tuple of (latitude, longitude) for the destination.
    :return: A dict of the travel time in seconds and sections of the journey
        with GeoJSON paths. Returns ``None`` if it could not fetch it.

    .. note ::

        Uses the Navitia API. Requires a ``navitia_api_key`` field to be
        filled-in in the ``config``.
    """
    travel_time = None

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

            journeys = req.json()["journeys"][0]
            travel_time = journeys["durations"]["total"]
            sections = []
            for section in journeys["sections"]:
                if section["type"] == "public_transport":
                    # Public transport
                    sections.append({
                        "geojson": section["geojson"],
                        "color": (
                            section["display_informations"].get("color", None)
                        )
                    })
                elif section["type"] == "street_network":
                    # Walking
                    sections.append({
                        "geojson": section["geojson"],
                        "color": None
                    })
                else:
                    # Skip anything else
                    continue
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
    if travel_time:
        return {
            "time": travel_time,
            "sections": sections
        }
    return None


def timeit(func):
    """
    A decorator that logs how much time was spent in the function.
    """
    def wrapped(*args, **kwargs):
        """
        The wrapped function
        """
        before = time.time()
        res = func(*args, **kwargs)
        runtime = time.time() - before
        LOGGER.info("%s -- Execution took %s seconds.", func.__name__, runtime)
        return res
    return wrapped
