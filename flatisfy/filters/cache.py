# coding: utf-8
"""
Caching function for pictures.
"""

from __future__ import absolute_import, print_function, unicode_literals

import collections
import hashlib
import os
import requests
from io import BytesIO

import PIL.Image


class MemoryCache(object):
    """
    A cache in memory.
    """
    @staticmethod
    def on_miss(key):
        """
        Method to be called whenever an object is requested from the cache but
        was not already cached. Typically, make a HTTP query to fetch it.

        :param key: Key of the requested object.
        :return: The object content.
        """
        raise NotImplementedError

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.map = collections.OrderedDict()

    def get(self, key):
        """
        Get an element from cache. Eventually call ``on_miss`` if the item is
        not already cached.

        :param key: Key of the element to retrieve.
        :return: Requested element.
        """
        cached = self.map.get(key, None)
        if cached is not None:
            self.hits += 1
            return cached

        item = self.map[key] = self.on_miss(key)
        self.misses += 1
        return item

    def total(self):
        """
        Get the total number of calls (with hits to the cache, or miss and
        fetching with ``on_miss``) to the cache.

        :return: Total number of item accessing.
        """
        return self.hits + self.misses

    def hit_rate(self):
        """
        Get the hit rate, that is the rate at which we requested an item which
        was already in the cache.

        :return: The hit rate, in percents.
        """
        assert self.total() > 0
        return 100 * self.hits // self.total()

    def miss_rate(self):
        """
        Get the miss rate, that is the rate at which we requested an item which
        was not already in the cache.

        :return: The miss rate, in percents.
        """
        assert self.total() > 0
        return 100 * self.misses // self.total()


class ImageCache(MemoryCache):
    """
    A cache for images, stored in memory.
    """
    @staticmethod
    def compute_filename(url):
        """
        Compute filename (hash of the URL) for the cached image.

        :param url: The URL of the image.
        :return: The filename, with its extension.
        """
        # Always store as JPEG
        return "%s.jpg" % hashlib.sha1(url.encode("utf-8")).hexdigest()

    def on_miss(self, url):
        """
        Helper to actually retrieve photos if not already cached.
        """
        # If two many items in the cache, pop one
        if len(self.map.keys()) > self.max_items:
            self.map.popitem(last=False)

        # Try to load from local folder
        if self.storage_dir:
            filepath = os.path.join(
                self.storage_dir,
                self.compute_filename(url)
            )
            if os.path.isfile(filepath):
                return PIL.Image.open(filepath)
        # Otherwise, fetch it
        req = requests.get(url)
        try:
            req.raise_for_status()
            image = PIL.Image.open(BytesIO(req.content))
            if self.storage_dir:
                image.save(filepath, format=image.format)
            return image
        except (requests.HTTPError, IOError):
            return None

    def __init__(self, max_items=200, storage_dir=None):
        """
        :param max_items: Max number of items in the cache, to prevent Out Of
            Memory errors.
        :param storage_dir: Directory in which images should be stored.
        """
        self.max_items = max_items
        self.storage_dir = storage_dir
        if self.storage_dir and not os.path.isdir(self.storage_dir):
            os.makedirs(self.storage_dir)
        super(ImageCache, self).__init__()
