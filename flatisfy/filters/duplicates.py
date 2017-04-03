# coding: utf-8
"""
Filtering functions to detect and merge duplicates.
"""
from __future__ import absolute_import, print_function, unicode_literals

import collections

from flatisfy import tools


def detect(flats_list, key="id", merge=True):
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

    :return: A deduplicated list of flat dicts.
    """
    # TODO: Keep track of found duplicates?
    # ``seen`` is a dict mapping aggregating the flats by the deduplication
    # keys. We basically make buckets of flats for every key value. Flats in
    # the same bucket should be merged together afterwards.
    seen = collections.defaultdict(list)
    for flat in flats_list:
        seen[flat.get(key, None)].append(flat)

    # Generate the unique flats list based on these buckets
    unique_flats_list = []
    for flat_key, matching_flats in seen.items():
        if flat_key is None:
            # If the key is None, it means Weboob could not load the data. In
            # this case, we consider every matching item as being independant
            # of the others, to avoid over-deduplication.
            unique_flats_list.extend(matching_flats)
        else:
            # Otherwise, check the policy
            if merge:
                # If a merge is requested, do the merge
                unique_flats_list.append(
                    tools.merge_dicts(*matching_flats)
                )
            else:
                # Otherwise, just keep any of them
                unique_flats_list.append(matching_flats[0])
    return unique_flats_list
