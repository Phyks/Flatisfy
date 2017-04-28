# coding: utf-8
"""
Filtering functions to detect and merge duplicates.
"""
from __future__ import absolute_import, print_function, unicode_literals

import collections
import logging

from flatisfy import tools

LOGGER = logging.getLogger(__name__)

# Some backends give more infos than others. Here is the precedence we want to
# use.
BACKENDS_PRECEDENCE = [
    "seloger",
    "pap",
    "leboncoin",
    "explorimmo",
    "logicimmo",
    "entreparticuliers"
]


def detect(flats_list, key="id", merge=True, should_intersect=False):
    """
    Detect obvious duplicates within a given list of flats.

    There may be duplicates found, as some queries could overlap (especially
    since when asking for a given place, websites tend to return housings in
    nearby locations as well). We need to handle them, by either deleting the
    duplicates (``merge=False``) or merging them together in a single flat
    object.

    :param flats_list: A list of flats dicts.
    :param key: The flat dicts key on which the duplicate detection should be
    done.
    :param merge: Whether the found duplicates should be merged or we should
    only keep one of them.
    :param should_intersect: Set to ``True`` if the values in the flat dicts
    are lists and you want to deduplicate on non-empty intersection (typically
    if they have a common url).

    :return: A tuple of the deduplicated list of flat dicts and the list of all
    the flats objects that should be removed and considered as duplicates (they
    were already merged).
    """
    # ``seen`` is a dict mapping aggregating the flats by the deduplication
    # keys. We basically make buckets of flats for every key value. Flats in
    # the same bucket should be merged together afterwards.
    seen = collections.defaultdict(list)
    for flat in flats_list:
        if should_intersect:
            # We add each value separately. We will add some flats multiple
            # times, but we deduplicate again on id below to compensate.
            for value in flat.get(key, []):
                seen[value].append(flat)
        else:
            seen[flat.get(key, None)].append(flat)

    # Generate the unique flats list based on these buckets
    unique_flats_list = []
    # Keep track of all the flats that were removed by deduplication
    duplicate_flats = []

    for flat_key, matching_flats in seen.items():
        if flat_key is None:
            # If the key is None, it means Weboob could not load the data. In
            # this case, we consider every matching item as being independant
            # of the others, to avoid over-deduplication.
            unique_flats_list.extend(matching_flats)
        else:
            # Sort matching flats by backend precedence
            matching_flats.sort(
                key=lambda flat: next(
                    i for (i, backend) in enumerate(BACKENDS_PRECEDENCE)
                    if flat["id"].endswith(backend)
                ),
                reverse=True
            )

            if len(matching_flats) > 1:
                LOGGER.info("Found duplicates using key \"%s\": %s.",
                            key,
                            [flat["id"] for flat in matching_flats])
            # Otherwise, check the policy
            if merge:
                # If a merge is requested, do the merge
                unique_flats_list.append(
                    tools.merge_dicts(*matching_flats)
                )
            else:
                # Otherwise, just keep the most important of them
                unique_flats_list.append(matching_flats[-1])

            # The ID of the added merged flat will be the one of the last item
            # in ``matching_flats``. Then, any flat object that was before in
            # the ``matching_flats`` list is to be considered as a duplicate
            # and should have a ``duplicate`` status.
            duplicate_flats.extend(matching_flats[:-1])

    if should_intersect:
        # We added some flats twice with the above method, let's deduplicate on
        # id.
        unique_flats_list, _ = detect(unique_flats_list, key="id", merge=True,
                                      should_intersect=False)

    return unique_flats_list, duplicate_flats


def deep_detect(flats_list):
    """
    TODO
    """
    for i, flat1 in enumerate(flats_list):
        for j, flat2 in enumerate(flats_list):
            if i < j:
                continue

            n_common_items = 0
            try:
                # They should have the same area, up to one unit
                assert abs(flat1["area"] - flat2["area"]) < 1
                n_common_items += 1

                # They should be at the same price, up to one unit
                assert abs(flat1["cost"] - flat2["cost"]) < 1
                n_common_items += 1

                # They should have the same number of bedrooms if this was
                # fetched for both
                if flat1["bedrooms"] and flat2["bedrooms"]:
                    assert flat1["bedrooms"] == flat2["bedrooms"]
                    n_common_items += 1

                # They should have the same utilities (included or excluded for
                # both of them), if this was fetched for both
                if flat1["utilities"] and flat2["utilities"]:
                    assert flat1["utilities"] == flat2["utilities"]
                    n_common_items += 1

                # They should have the same number of rooms if it was fetched
                # for both of them
                if flat1["rooms"] and flat2["rooms"]:
                    assert flat1["rooms"] == flat2["rooms"]
                    n_common_items += 1

                # They should have the same postal code, if available
                if (
                        flat1["flatisfy"].get("postal_code", None) and
                        flat2["flatisfy"].get("postal_code", None)
                ):
                    assert (
                        flat1["flatisfy"]["postal_code"] ==
                        flat2["flatisfy"]["postal_code"]
                    )
                    n_common_items += 1

                # They should have the same phone number if it was fetched for
                # both
                if flat1["phone"] and flat2["phone"]:
                    homogeneize_phone_number = lambda number: (
                        number.replace(".", "").replace(" ", "")
                    )
                    pass  # TODO: Homogeneize phone numbers

                # TODO: Compare texts (one is included in another? fuzzymatch?)
            except AssertionError:
                # Skip and consider as not duplicates whenever the conditions
                # are not met
                continue
            except TypeError:
                # TypeError occurs when an area or a cost is None, which should
                # not be considered as duplicates
                continue

            # TODO: Check the number of common items

            # TODO: Merge flats

            # TODO: Compare photos
