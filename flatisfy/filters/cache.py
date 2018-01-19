# coding: utf-8

"""
Caching function for pictures.
"""

from __future__ import absolute_import, print_function, unicode_literals

import requests


class MemoryCache(object):
    """
    A cache in memory.
    """

    @staticmethod
    def on_miss(key):
        raise NotImplementedError

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.map = {}

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
    def on_miss(url):
        """
        Helper to actually retrieve photos if not already cached.
        """
        return requests.get(url)
