# coding: utf-8
"""
Filtering functions to handle flatisfy-specific metadata.

This includes functions to guess metadata (postal codes, stations) from the
actual fetched data.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import re

from flatisfy import data
from flatisfy import tools
from flatisfy.models.postal_code import PostalCode
from flatisfy.models.public_transport import PublicTransport


LOGGER = logging.getLogger(__name__)


def init(flats_list, constraint):
    """
    Create a flatisfy key containing a dict of metadata fetched by flatisfy for
    each flat in the list. Also perform some basic transform on flat objects to
    prepare for the metadata fetching.

    :param flats_list: A list of flats dict.
    :param constraint: The constraint that the ``flats_list`` should satisfy.
    :return: The updated list
    """
    for flat in flats_list:
        # Init flatisfy key
        if "flatisfy" not in flat:
            flat["flatisfy"] = {}
        if "constraint" not in flat["flatisfy"]:
            flat["flatisfy"]["constraint"] = constraint
        # Move url key to urls
        if "urls" not in flat:
            if "url" in flat:
                flat["urls"] = [flat["url"]]
            else:
                flat["urls"] = []
        # Create merged_ids key
        if "merged_ids" not in flat:
            flat["merged_ids"] = [flat["id"]]

    return flats_list


def fuzzy_match(query, choices, limit=3, threshold=75):
    """
    Custom search for the best element in choices matching the query.

    :param query: The string to match.
    :param choices: The list of strings to match with.
    :param limit: The maximum number of items to return. Set to ``None`` to
        return all values above threshold.
    :param threshold: The score threshold to use.

    :return: Tuples of matching items and associated confidence.

    .. note ::

        This function works by removing any fancy character from the ``query``
        and ``choices`` strings (replacing any non alphabetic and non numeric
        characters by space), converting to lower case and normalizing them
        (collapsing multiple spaces etc). It also converts any roman numerals
        to decimal system. It then compares the string and look for the longest
        string in ``choices`` which is a substring of ``query``. The longest
        one gets a confidence of 100. The shorter ones get a confidence
        proportional to their length.

    .. seealso :: flatisfy.tools.normalize_string

    Example::

        >>> match("Paris 14ème", ["Ris", "ris", "Paris 14"], limit=1)
        [("Paris 14", 100)

        >>> match( \
                "Saint-Jacques, Denfert-Rochereau (Colonel Rol-Tanguy), " \
                "Mouton-Duvernet", \
                ["saint-jacques", "denfert rochereau", "duvernet", "toto"], \
                limit=4 \
            )
        [('denfert rochereau', 100), ('saint-jacques', 76)]
    """
    # TODO: Is there a better confidence measure?
    normalized_query = tools.normalize_string(query)
    normalized_choices = [tools.normalize_string(choice) for choice in choices]

    # Remove duplicates in the choices list
    unique_normalized_choices = tools.uniqify(normalized_choices)

    # Get the matches (normalized strings)
    # Keep only ``limit`` matches.
    matches = sorted(
        [
            (choice, len(choice))
            for choice in tools.uniqify(unique_normalized_choices)
            if choice in normalized_query
        ],
        key=lambda x: x[1],
        reverse=True
    )
    if limit:
        matches = matches[:limit]

    # Update confidence
    if matches:
        max_confidence = max(match[1] for match in matches)
        matches = [
            (x[0], int(x[1] / max_confidence * 100))
            for x in matches
        ]

    # Convert back matches to original strings
    # Also filter out matches below threshold
    matches = [
        (choices[normalized_choices.index(x[0])], x[1])
        for x in matches
        if x[1] >= threshold
    ]

    return matches


def guess_postal_code(flats_list, constraint, config, distance_threshold=20000):
    """
    Try to guess the postal code from the location of the flats.

    :param flats_list: A list of flats dict.
    :param constraint: The constraint that the ``flats_list`` should satisfy.
    :param config: A config dict.
    :param distance_threshold: Maximum distance in meters between the
        constraint postal codes (from config) and the one found by this
        function, to avoid bad fuzzy matching. Can be ``None`` to disable
        thresholding.

    :return: An updated list of flats dict with guessed postal code.
    """
    opendata = {
        "postal_codes": data.load_data(PostalCode, constraint, config)
    }

    for flat in flats_list:
        location = flat.get("location", None)
        if not location:
            # Skip everything if empty location
            LOGGER.info(
                (
                    "No location field for flat %s, skipping postal "
                    "code lookup."
                ),
                flat["id"]
            )
            continue

        postal_code = None
        # Try to find a postal code directly
        try:
            postal_code = re.search(r"[0-9]{5}", location)
            assert postal_code is not None
            postal_code = postal_code.group(0)

            # Check the postal code is within the db
            assert postal_code in [x.postal_code
                                   for x in opendata["postal_codes"]]

            LOGGER.info(
                "Found postal code in location field for flat %s: %s.",
                flat["id"], postal_code
            )
        except AssertionError:
            postal_code = None

        # If not found, try to find a city
        if not postal_code:
            # Find all fuzzy-matching cities
            matched_cities = fuzzy_match(
                location,
                [x.name for x in opendata["postal_codes"]],
                limit=None
            )
            if matched_cities:
                # Find associated postal codes
                matched_postal_codes = []
                for matched_city_name, _ in matched_cities:
                    postal_code_objects_for_city = [
                        x for x in opendata["postal_codes"]
                        if x.name == matched_city_name
                    ]
                    matched_postal_codes.extend(
                        pc.postal_code
                        for pc in postal_code_objects_for_city
                    )
                # Try to match them with postal codes in config constraint
                matched_postal_codes_in_config = (
                    set(matched_postal_codes) & set(constraint["postal_codes"])
                )
                if matched_postal_codes_in_config:
                    # If there are some matched postal codes which are also in
                    # config, use them preferentially. This avoid ignoring
                    # incorrectly some flats in cities with multiple postal
                    # codes, see #110.
                    postal_code = next(iter(matched_postal_codes_in_config))
                else:
                    # Otherwise, simply take any matched postal code.
                    postal_code = matched_postal_codes[0]
                LOGGER.info(
                    ("Found postal code in location field through city lookup "
                     "for flat %s: %s."),
                    flat["id"], postal_code
                )

        # Check that postal code is not too far from the ones listed in config,
        # limit bad fuzzy matching
        if postal_code and distance_threshold:
            distance = min(
                tools.distance(
                    next(
                        (x.lat, x.lng)
                        for x in opendata["postal_codes"]
                        if x.postal_code == postal_code
                    ),
                    next(
                        (x.lat, x.lng)
                        for x in opendata["postal_codes"]
                        if x.postal_code == constraint_postal_code
                    )
                )
                for constraint_postal_code in constraint["postal_codes"]
            )

            if distance > distance_threshold:
                LOGGER.info(
                    ("Postal code %s found for flat %s is off-constraints "
                     "(distance is %dm > %dm). Let's consider it is an "
                     "artifact match and keep the post without this postal "
                     "code."),
                    postal_code,
                    flat["id"],
                    int(distance),
                    int(distance_threshold)
                )
                postal_code = None

        # Store it
        if postal_code:
            existing_postal_code = flat["flatisfy"].get("postal_code", None)
            if existing_postal_code and existing_postal_code != postal_code:
                LOGGER.warning(
                    "Replacing previous postal code %s by %s for flat %s.",
                    existing_postal_code, postal_code, flat["id"]
                )
            flat["flatisfy"]["postal_code"] = postal_code
        else:
            LOGGER.info("No postal code found for flat %s.", flat["id"])

    return flats_list


def guess_stations(flats_list, constraint, config):
    """
    Try to match the station field with a list of available stations nearby.

    :param flats_list: A list of flats dict.
    :param constraint: The constraint that the ``flats_list`` should satisfy.
    :param config: A config dict.

    :return: An updated list of flats dict with guessed nearby stations.
    """
    distance_threshold = config['max_distance_housing_station']
    opendata = {
        "postal_codes": data.load_data(PostalCode, constraint, config),
        "stations": data.load_data(PublicTransport, constraint, config)
    }

    for flat in flats_list:
        flat_station = flat.get("station", None)

        if not flat_station:
            # Skip everything if empty station
            LOGGER.info(
                "No stations field for flat %s, skipping stations lookup.",
                flat["id"]
            )
            continue

        matched_stations = fuzzy_match(
            flat_station,
            [x.name for x in opendata["stations"]],
            limit=10,
            threshold=50
        )

        # Filter out the stations that are obviously too far and not well
        # guessed
        good_matched_stations = []
        postal_code = flat["flatisfy"].get("postal_code", None)
        if postal_code:
            # If there is a postal code, check that the matched station is
            # closed to it
            postal_code_gps = next(
                (x.lat, x.lng)
                for x in opendata["postal_codes"]
                if x.postal_code == postal_code
            )
            for station in matched_stations:
                # Note that multiple stations with the same name exist in a
                # city, hence the list of stations objects for a given matching
                # station name.
                stations_objects = [
                    x for x in opendata["stations"] if x.name == station[0]
                ]
                for station_data in stations_objects:
                    distance = tools.distance(
                        (station_data.lat, station_data.lng),
                        postal_code_gps
                    )
                    if distance < distance_threshold:
                        # If at least one of the coordinates for a given
                        # station is close enough, that's ok and we can add
                        # the station
                        good_matched_stations.append({
                            "key": station[0],
                            "name": station_data.name,
                            "confidence": station[1],
                            "gps": (station_data.lat, station_data.lng)
                        })
                        break
                    LOGGER.info(
                        ("Station %s is too far from flat %s (%dm > %dm), "
                         "discarding this station."),
                        station[0],
                        flat["id"],
                        int(distance),
                        int(distance_threshold)
                    )
        else:
            LOGGER.info(
                "No postal code for flat %s, skipping stations detection.",
                flat["id"]
            )

        if not good_matched_stations:
            # No stations found, log it and cotninue with next housing
            LOGGER.info(
                "No stations found for flat %s, matching %s.",
                flat["id"],
                flat["station"]
            )
            continue

        LOGGER.info(
            "Found stations for flat %s: %s (matching %s).",
            flat["id"],
            ", ".join(x["name"] for x in good_matched_stations),
            flat["station"]
        )

        # If some stations were already filled in and the result is different,
        # display some warning to the user
        if (
                "matched_stations" in flat["flatisfy"] and
                (
                    # Do a set comparison, as ordering is not important
                    set([
                        station["name"]
                        for station in flat["flatisfy"]["matched_stations"]
                    ]) !=
                    set([
                        station["name"]
                        for station in good_matched_stations
                    ])
                )
        ):
            LOGGER.warning(
                "Replacing previously fetched stations for flat %s. Found "
                "stations differ from the previously found ones.",
                flat["id"]
            )

        flat["flatisfy"]["matched_stations"] = good_matched_stations

    return flats_list


def compute_travel_times(flats_list, constraint, config):
    """
    Compute the travel time between each flat and the points listed in the
    constraints.

    :param flats_list: A list of flats dict.
    :param constraint: The constraint that the ``flats_list`` should satisfy.
    :param config: A config dict.

    :return: An updated list of flats dict with computed travel times.

    .. note :: Requires a Navitia or CityMapper API key in the config.
    """
    for flat in flats_list:
        if not flat["flatisfy"].get("matched_stations", []):
            # Skip any flat without matched stations
            LOGGER.info(
                "Skipping travel time computation for flat %s. No matched "
                "stations.",
                flat["id"]
            )
            continue

        if "time_to" not in flat["flatisfy"]:
            # Ensure time_to key is initialized
            flat["flatisfy"]["time_to"] = {}

        # For each place, loop over the stations close to the flat, and find
        # the minimum travel time.
        for place_name, place in constraint["time_to"].items():
            time_to_place = None
            for station in flat["flatisfy"]["matched_stations"]:
                time_from_station = tools.get_travel_time_between(
                    station["gps"],
                    place["gps"],
                    config
                )
                if (
                        time_from_station and
                        (
                            time_from_station["time"] < time_to_place or
                            time_to_place is None
                        )
                ):
                    time_to_place = time_from_station["time"]

            if time_to_place:
                LOGGER.info(
                    "Travel time between %s and flat %s is %ds.",
                    place_name, flat["id"], time_to_place
                )
                flat["flatisfy"]["time_to"][place_name] = time_to_place
    return flats_list
