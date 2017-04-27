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
