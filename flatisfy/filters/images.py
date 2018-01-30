# coding: utf-8
"""
Filtering functions to handle images.

This includes functions to download images.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os

from flatisfy.filters.cache import ImageCache


LOGGER = logging.getLogger(__name__)


def download_images(flats_list, config):
    """
    Download images for all flats in the list, to serve them locally.

    :param flats_list: A list of flats dicts.
    :param config: A config dict.
    """
    photo_cache = ImageCache(
        storage_dir=os.path.join(config["data_directory"], "images")
    )
    flats_list_length = len(flats_list)
    for i, flat in enumerate(flats_list):
        LOGGER.info(
            "Downloading photos for flat %d/%d.", i + 1, flats_list_length
        )
        for photo in flat["photos"]:
            # Download photo
            image = photo_cache.get(photo["url"])
            # And store the local image
            # Only add it if fetching was successful
            if image:
                photo["local"] = photo_cache.compute_filename(photo["url"])
