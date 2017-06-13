# coding: utf-8

"""
Caching function for pictures.
"""

from __future__ import absolute_import, print_function, unicode_literals

import requests

class MemoryCache(object):
    def __init__(self, on_miss):
        self.hits = 0
        self.misses = 0
        self.map = {}
        self.on_miss = on_miss

    def get(self, key):
        cached = self.map.get(key, None)
        if cached is not None:
            self.hits += 1
            return cached

        item = self.map[key] = self.on_miss(key)
        self.misses += 1
        return item

    def total(self):
        return self.hits + self.misses

    def hit_rate(self):
        assert self.total() > 0
        return 100 * self.hits // self.total()

    def miss_rate(self):
        assert self.total() > 0
        return 100 * self.misses // self.total()

class ImageCache(MemoryCache):
    @staticmethod
    def retrieve_photo(url):
        return requests.get(url)

    def __init__(self):
        super(self.__class__, self).__init__(on_miss=ImageCache.retrieve_photo)
