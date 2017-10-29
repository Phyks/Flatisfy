# coding: utf-8
"""
This module contains all the filtering functions. It exposes ``first_pass`` and
``second_pass`` functions which are a set of filters applied during the first
pass and the second pass.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging

from flatisfy import tools
from flatisfy.filters import duplicates
from flatisfy.filters import metadata


LOGGER = logging.getLogger(__name__)


def refine_with_housing_criteria(flats_list, constraint):
    """
    Filter a list of flats according to criteria.

    Housings posts websites tend to return broader results that what was
    actually asked for. Then, we should filter out the list to match the
    user criteria, and avoid exposing unwanted flats.

    :param flats_list: A list of flats dict to filter.
    :param constraint: The constraint that the ``flats_list`` should satisfy.
    :return: A tuple of flats to keep and flats to delete.
    """
    # For each flat, the associated `is_ok` value indicate whether it should be
    # kept or discarded.
    is_ok = [True for _ in flats_list]

    for i, flat in enumerate(flats_list):
        # Check postal code
        postal_code = flat["flatisfy"].get("postal_code", None)
        if (
                postal_code and
                postal_code not in constraint["postal_codes"]
        ):
            LOGGER.info("Postal code for flat %s is out of range.", flat["id"])
            is_ok[i] = is_ok[i] and False

        # Check time_to
        for place_name, time in flat["flatisfy"].get("time_to", {}).items():
            time = time["time"]
            is_within_interval = tools.is_within_interval(
                time,
                *(constraint["time_to"][place_name]["time"])
            )
            if not is_within_interval:
                LOGGER.info("Flat %s is too far from place %s: %ds.",
                            flat["id"], place_name, time)
            is_ok[i] = is_ok[i] and is_within_interval

        # Check other fields
        for field in ["area", "cost", "rooms", "bedrooms"]:
            interval = constraint[field]
            is_within_interval = tools.is_within_interval(
                flat.get(field, None),
                *interval
            )
            if not is_within_interval:
                LOGGER.info("%s for flat %s is out of range.",
                            field.capitalize(), flat["id"])
            is_ok[i] = is_ok[i] and is_within_interval

    return (
        [
            flat
            for i, flat in enumerate(flats_list)
            if is_ok[i]
        ],
        [
            flat
            for i, flat in enumerate(flats_list)
            if not is_ok[i]
        ]
    )


def refine_with_details_criteria(flats_list, constraint):
    """
    Filter a list of flats according to the criteria which require the full
    details to be fetched. These include minimum number of photos and terms
    that should appear in description.

    .. note :: This has to be done in a separate function and not with the
    other criterias as photos and full description are only fetched in the
    second pass.

    :param flats_list: A list of flats dict to filter.
    :param constraint: The constraint that the ``flats_list`` should satisfy.
    :return: A tuple of flats to keep and flats to delete.
    """
    # For each flat, the associated `is_ok` value indicate whether it should be
    # kept or discarded.
    is_ok = [True for _ in flats_list]

    for i, flat in enumerate(flats_list):
        # Check number of pictures
        has_enough_photos = tools.is_within_interval(
            flat.get('photos', []),
            constraint['minimum_nb_photos'],
            None
        )
        if not has_enough_photos:
            LOGGER.info(
                "Flat %s only has %d photos, it should have at least %d.",
                flat["id"],
                len(flat['photos']),
                constraint['minimum_nb_photos']
            )
            is_ok[i] = False

        has_terms_in_description = True
        if constraint["description_should_contain"]:
            has_terms_in_description = all(
                term in flat['text']
                for term in constraint["description_should_contain"]
            )
        if not has_terms_in_description:
            LOGGER.info(
                ("Description for flat %s does not contain all the required "
                 "terms."),
                flat["id"]
            )
            is_ok[i] = False

    return (
        [
            flat
            for i, flat in enumerate(flats_list)
            if is_ok[i]
        ],
        [
            flat
            for i, flat in enumerate(flats_list)
            if not is_ok[i]
        ]
    )


@tools.timeit
def first_pass(flats_list, constraint, config):
    """
    First filtering pass.

    Flatboob only fetches data from the listing of the available housing. Then,
    we should do a first pass to filter based on the already available data and
    only request more data for the remaining housings.

    :param flats_list: A list of flats dict to filter.
    :param constraint: The constraint that the ``flats_list`` should satisfy.
    :param config: A config dict.
    :return: A dict mapping flat status and list of flat objects.
    """
    LOGGER.info("Running first filtering pass.")

    # Handle duplicates based on ids
    # Just remove them (no merge) as they should be the exact same object.
    flats_list, duplicates_by_id = duplicates.detect(
        flats_list, key="id", merge=False, should_intersect=False
    )
    # Also merge duplicates based on urls (these may come from different
    # flatboob backends)
    # This is especially useful as some websites such as entreparticuliers
    # contains a lot of leboncoin housings posts.
    flats_list, duplicates_by_urls = duplicates.detect(
        flats_list, key="urls", merge=True, should_intersect=True
    )

    # Guess the postal codes
    flats_list = metadata.guess_postal_code(flats_list, constraint, config)
    # Try to match with stations
    flats_list = metadata.guess_stations(flats_list, constraint, config)
    # Remove returned housing posts that do not match criteria
    flats_list, ignored_list = refine_with_housing_criteria(flats_list,
                                                            constraint)

    return {
        "new": flats_list,
        "ignored": ignored_list,
        "duplicate": duplicates_by_id + duplicates_by_urls
    }

@tools.timeit
def second_pass(flats_list, constraint, config):
    """
    Second filtering pass.

    This pass is expected to have as most information as possible on the
    available housings. Plus it runs after first pass which already
    consolidated data.

    It should consolidate everything and try to extract as many data as
    possible from the fetched housings.

    :param flats_list: A list of flats dict to filter.
    :param constraint: The constraint that the ``flats_list`` should satisfy.
    :param config: A config dict.
    :return: A dict mapping flat status and list of flat objects.
    """
    LOGGER.info("Running second filtering pass.")
    # Assumed to run after first pass, so there should be no obvious duplicates
    # left and we already tried to find postal code and nearby stations.

    # Confirm postal code
    flats_list = metadata.guess_postal_code(flats_list, constraint, config)

    # Better match with stations (confirm and check better)
    flats_list = metadata.guess_stations(flats_list, constraint, config)

    # Compute travel time to specified points
    flats_list = metadata.compute_travel_times(flats_list, constraint, config)

    # Remove returned housing posts that do not match criteria
    flats_list, ignored_list = refine_with_housing_criteria(flats_list,
                                                            constraint)

    # Remove returned housing posts which do not match criteria relying on
    # fetched details.
    flats_list, ignored_list = refine_with_details_criteria(flats_list,
                                                            constraint)

    return {
        "new": flats_list,
        "ignored": ignored_list,
        "duplicate": []
    }

@tools.timeit
def third_pass(flats_list, config):
    """
    Third filtering pass.

    This pass is expected to perform deep duplicate detection on available
    flats.

    :param flats_list: A list of flats dict to filter.
    :param config: A config dict.
    :return: A dict mapping flat status and list of flat objects.
    """
    LOGGER.info("Running third filtering pass.")

    # Deduplicate the list using every available data
    flats_list, duplicate_flats = duplicates.deep_detect(flats_list)

    return {
        "new": flats_list,
        "ignored": [],
        "duplicate": duplicate_flats
    }
