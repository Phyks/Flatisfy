# coding: utf-8
"""
Filtering functions to detect and merge duplicates.
"""
from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools
import logging
import re

from io import BytesIO

import imagehash
import PIL.Image
import requests

from flatisfy import tools
from flatisfy.constants import BACKENDS_BY_PRECEDENCE
from flatisfy.filters.cache import ImageCache

LOGGER = logging.getLogger(__name__)


def homogeneize_phone_number(number):
    """
    Homogeneize the phone numbers, by stripping any space, dash or dot as well
    as the international prefix. Assumes it is dealing with French phone
    numbers (starting with a zero and having 10 characters).

    :param number: The phone number to homogeneize.
    :return: The cleaned phone number. ``None`` if the number is not valid.
    """
    if not number:
        return None
    number = number.replace(".", "")
    number = number.replace(" ", "")
    number = number.replace("-", "")
    number = number.replace("(", "")
    number = number.replace(")", "")
    number = re.sub(r'^\+\d\d', "", number)

    if not number.startswith("0"):
        number = "0" + number

    if len(number) != 10:
        return None

    return number


def find_number_common_photos(photo_cache, flat1_photos, flat2_photos):
    """
    Compute the number of common photos between the two lists of photos for the
    flats.

    Fetch the photos and compare them with dHash method.

    :param flat1_photos: First list of flat photos. Each photo should be a
        ``dict`` with a ``url`` key.
    :param flat2_photos: First list of flat photos. Each photo should be a
        ``dict`` with a ``url`` key.
    :return: The found number of common photos.
    """
    n_common_photos = 0

    for photo1, photo2 in itertools.product(flat1_photos, flat2_photos):
        try:
            req1 = photo_cache.get(photo1["url"])
            im1 = PIL.Image.open(BytesIO(req1.content))
            hash1 = imagehash.average_hash(im1)

            req2 = photo_cache.get(photo2["url"])
            im2 = PIL.Image.open(BytesIO(req2.content))
            hash2 = imagehash.average_hash(im2)

            if hash1 - hash2 == 0:
                n_common_photos += 1
        except (IOError, requests.exceptions.RequestException):
            pass

    return n_common_photos


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
        are lists and you want to deduplicate on non-empty intersection
        (typically if they have a common url).

    :return: A tuple of the deduplicated list of flat dicts and the list of all
        the flats objects that should be removed and considered as duplicates
        (they were already merged).
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
                    i for (i, backend) in enumerate(BACKENDS_BY_PRECEDENCE)
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

def get_duplicate_score(flat1, flat2, photo_cache):
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
                "flatisfy" in flat1 and "flatisfy" in flat2 and
                flat1["flatisfy"].get("postal_code", None) and
                flat2["flatisfy"].get("postal_code", None)
        ):
            assert (
                flat1["flatisfy"]["postal_code"] ==
                flat2["flatisfy"]["postal_code"]
            )
            n_common_items += 1

        # TODO: Better text comparison (one included in the other, fuzzymatch)
        flat1_text = tools.normalize_string(flat1.get("text", ""))
        flat2_text = tools.normalize_string(flat2.get("text", ""))
        if flat1_text and flat2_text and flat1_text == flat2_text:
            n_common_items += 1

        # They should have the same phone number if it was fetched for
        # both
        flat1_phone = homogeneize_phone_number(flat1["phone"])
        flat2_phone = homogeneize_phone_number(flat2["phone"])
        if flat1_phone and flat2_phone:
            assert flat1_phone == flat2_phone
            n_common_items += 10  # Counts much more than the rest

        # They should have at least one photo in common if there
        # are some photos
        if flat1.get("photos", []) and flat2.get("photos", []):
            n_common_photos = find_number_common_photos(
                photo_cache,
                flat1["photos"],
                flat2["photos"]
            )
            assert n_common_photos > 1

            min_number_photos = min(len(flat1["photos"]),
                                    len(flat2["photos"]))

            # Either all the photos are the same, or there are at least
            # three common photos.
            if n_common_photos == min_number_photos:
                n_common_items += 15
            else:
                n_common_items += 5 * min(n_common_photos, 3)

        # If the two flats are from the same website and have a
        # different float part, consider they cannot be duplicates. See
        # https://framagit.org/phyks/Flatisfy/issues/100.
        both_are_from_same_backend = (
            flat1["id"].split("@")[-1] == flat2["id"].split("@")[-1]
        )
        both_have_float_part = (
            (flat1["area"] % 1) > 0 and (flat2["area"] % 1) > 0
        )
        both_have_equal_float_part = (
            (flat1["area"] % 1) == (flat2["area"] % 1)
        )
        if both_have_float_part and both_are_from_same_backend:
            assert both_have_equal_float_part
    except (AssertionError, TypeError):
        # Skip and consider as not duplicates whenever the conditions
        # are not met
        # TypeError occurs when an area or a cost is None, which should
        # not be considered as duplicates
        n_common_items = 0

    return n_common_items

def deep_detect(flats_list, config):
    """
    Deeper detection of duplicates based on any available data.

    :param flats_list: A list of flats dicts.
    :param config: A config dict.
    :return: A tuple of the deduplicated list of flat dicts and the list of all
        the flats objects that should be removed and considered as duplicates
        (they were already merged).
    """

    photo_cache = ImageCache()

    LOGGER.info("Running deep duplicates detection.")
    matching_flats = collections.defaultdict(list)
    for i, flat1 in enumerate(flats_list):
        matching_flats[flat1["id"]].append(flat1["id"])
        for j, flat2 in enumerate(flats_list):
            if i <= j:
                continue

            if flat2["id"] in matching_flats[flat1["id"]]:
                continue

            n_common_items = get_duplicate_score(flat1, flat2, photo_cache)

            # Minimal score to consider they are duplicates
            if n_common_items >= config["duplicate_threshold"]:
                # Mark flats as duplicates
                LOGGER.info(
                    ("Found duplicates using deep detection: (%s, %s). "
                     "Score is %d."),
                    flat1["id"],
                    flat2["id"],
                    n_common_items
                )
                matching_flats[flat1["id"]].append(flat2["id"])
                matching_flats[flat2["id"]].append(flat1["id"])

    if photo_cache.total():
        LOGGER.debug("Photo cache: hits: %d%% / misses: %d%%.",
                     photo_cache.hit_rate(),
                     photo_cache.miss_rate())

    seen_ids = []
    duplicate_flats = []
    unique_flats_list = []
    for flat_id in [flat["id"] for flat in flats_list]:
        if flat_id in seen_ids:
            continue

        seen_ids.extend(matching_flats[flat_id])
        to_merge = sorted(
            [
                flat
                for flat in flats_list
                if flat["id"] in matching_flats[flat_id]
            ],
            key=lambda flat: next(
                i for (i, backend) in enumerate(BACKENDS_BY_PRECEDENCE)
                if flat["id"].endswith(backend)
            ),
            reverse=True
        )
        unique_flats_list.append(tools.merge_dicts(*to_merge))
        # The ID of the added merged flat will be the one of the last item
        # in ``matching_flats``. Then, any flat object that was before in
        # the ``matching_flats`` list is to be considered as a duplicate
        # and should have a ``duplicate`` status.
        duplicate_flats.extend(to_merge[:-1])

    return unique_flats_list, duplicate_flats
