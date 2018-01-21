# coding: utf-8
"""
This module contains unit testing functions.
"""
import copy
import json
import logging
import os
import random
import sys
import unittest
import requests
import requests_mock

from flatisfy import tools
from flatisfy.filters import duplicates
from flatisfy.filters.cache import ImageCache
from flatisfy.constants import BACKENDS_BY_PRECEDENCE

LOGGER = logging.getLogger(__name__)
TESTS_DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/test_files/"


class LocalImageCache(ImageCache):
    """
    A local cache for images, stored in memory.
    """
    @staticmethod
    def on_miss(path):
        """
        Helper to actually retrieve photos if not already cached.
        """
        url = "mock://flatisfy" + path
        with requests_mock.Mocker() as mock:
            with open(path, "rb") as fh:
                mock.get(url, content=fh.read())
                return requests.get(url)


class TestTexts(unittest.TestCase):
    """
    Checks string normalizations.
    """
    def test_roman_numbers(self):
        """
        Checks roman numbers replacement.
        """
        self.assertEqual(
            "XIV",
            tools.convert_arabic_to_roman("14")
        )

        self.assertEqual(
            "MCMLXXXVII",
            tools.convert_arabic_to_roman("1987")
        )

        self.assertEqual(
            "Dans le XVe arrondissement",
            tools.convert_arabic_to_roman_in_text("Dans le 15e arrondissement")
        )

        self.assertEqual(
            "XXeme arr.",
            tools.convert_arabic_to_roman_in_text("20eme arr.")
        )

        self.assertEqual(
            "A AIX EN PROVENCE",
            tools.convert_arabic_to_roman_in_text("A AIX EN PROVENCE")
        )

        self.assertEqual(
            "Montigny Le Bretonneux",
            tools.convert_arabic_to_roman_in_text("Montigny Le Bretonneux")
        )

    def test_roman_numbers_in_text(self):
        """
        Checks conversion of roman numbers to arabic ones in string
        normalization.
        """
        self.assertEqual(
            "dans le XVe arrondissement",
            tools.normalize_string("Dans le 15e arrondissement")
        )

    def test_multiple_whitespaces(self):
        """
        Checks whitespaces are collapsed.
        """
        self.assertEqual(
            "avec ascenseur",
            tools.normalize_string("avec   ascenseur")
        )

    def test_accents(self):
        """
        Checks accents are replaced.
        """
        self.assertEqual(
            "eeeaui",
            tools.normalize_string(u"éèêàüï")
        )


class TestPhoneNumbers(unittest.TestCase):
    """
    Checks phone numbers normalizations.
    """
    def test_prefix(self):
        """
        Checks phone numbers with international prefixes.
        """
        self.assertEqual(
            "0605040302",
            duplicates.homogeneize_phone_number("+33605040302")
        )

    def test_dots_separators(self):
        """
        Checks phone numbers with dots.
        """
        self.assertEqual(
            "0605040302",
            duplicates.homogeneize_phone_number("06.05.04.03.02")
        )

    def test_spaces_separators(self):
        """
        Checks phone numbers with spaces.
        """
        self.assertEqual(
            "0605040302",
            duplicates.homogeneize_phone_number("06 05 04 03 02")
        )


class TestPhotos(unittest.TestCase):
    IMAGE_CACHE = LocalImageCache()  # pylint: disable=invalid-name
    HASH_THRESHOLD = 10  # pylint: disable=invalid-name

    def test_same_photo_twice(self):
        """
        Compares a photo against itself.
        """
        photo = {
            "url": TESTS_DATA_DIR + "127028739@seloger.jpg"
        }

        self.assertTrue(duplicates.compare_photos(
            photo,
            photo,
            TestPhotos.IMAGE_CACHE,
            TestPhotos.HASH_THRESHOLD
        ))

    def test_different_photos(self):
        """
        Compares two different photos.
        """
        self.assertFalse(duplicates.compare_photos(
            {"url": TESTS_DATA_DIR + "127028739@seloger.jpg"},
            {"url": TESTS_DATA_DIR + "127028739-2@seloger.jpg"},
            TestPhotos.IMAGE_CACHE,
            TestPhotos.HASH_THRESHOLD
        ))

        self.assertFalse(duplicates.compare_photos(
            {"url": TESTS_DATA_DIR + "127028739-2@seloger.jpg"},
            {"url": TESTS_DATA_DIR + "127028739-3@seloger.jpg"},
            TestPhotos.IMAGE_CACHE,
            TestPhotos.HASH_THRESHOLD
        ))

    def test_matching_photos(self):
        """
        Compares two matching photos with different size and source.
        """
        self.assertTrue(duplicates.compare_photos(
            {"url": TESTS_DATA_DIR + "127028739@seloger.jpg"},
            {"url": TESTS_DATA_DIR + "14428129@explorimmo.jpg"},
            TestPhotos.IMAGE_CACHE,
            TestPhotos.HASH_THRESHOLD
        ))

        self.assertTrue(duplicates.compare_photos(
            {"url": TESTS_DATA_DIR + "127028739-2@seloger.jpg"},
            {"url": TESTS_DATA_DIR + "14428129-2@explorimmo.jpg"},
            TestPhotos.IMAGE_CACHE,
            TestPhotos.HASH_THRESHOLD
        ))

        self.assertTrue(duplicates.compare_photos(
            {"url": TESTS_DATA_DIR + "127028739-3@seloger.jpg"},
            {"url": TESTS_DATA_DIR + "14428129-3@explorimmo.jpg"},
            TestPhotos.IMAGE_CACHE,
            TestPhotos.HASH_THRESHOLD
        ))

        self.assertTrue(duplicates.compare_photos(
            {"url": TESTS_DATA_DIR + "127028739@seloger.jpg"},
            {"url": TESTS_DATA_DIR + "127028739-watermark@seloger.jpg"},
            TestPhotos.IMAGE_CACHE,
            TestPhotos.HASH_THRESHOLD
        ))


class TestDuplicates(unittest.TestCase):
    """
    Checks duplicates detection.
    """
    DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS = 14  # pylint: disable=invalid-name
    DUPLICATES_MIN_SCORE_WITH_PHOTOS = 15  # pylint: disable=invalid-name
    HASH_THRESHOLD = 10  # pylint: disable=invalid-name
    IMAGE_CACHE = ImageCache()  # pylint: disable=invalid-name

    @staticmethod
    def generate_fake_flat():
        """
        Generates a fake flat post.
        """
        backend = BACKENDS_BY_PRECEDENCE[
            random.randint(0, len(BACKENDS_BY_PRECEDENCE) - 1)
        ]
        return {
            "id": str(random.randint(100000, 199999)) + "@" + backend,
            "phone": "0607080910",
            "rooms": random.randint(1, 4),
            "utilities": "",
            "area": random.randint(200, 1500) / 10,
            "cost": random.randint(100000, 300000),
            "bedrooms": random.randint(1, 4)
        }

    @staticmethod
    def load_files(file1, file2):
        """
        Load two files

        :return: A dict with two flats
        """
        with open(TESTS_DATA_DIR + file1 + ".json", "r") as flat_file:
            flat1 = json.loads(flat_file.read())

        with open(TESTS_DATA_DIR + file2 + ".json", "r") as flat_file:
            flat2 = json.loads(flat_file.read())

        return [flat1, flat2]

    def test_duplicates(self):
        """
        Two identical flats should be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        score = duplicates.get_duplicate_score(
            flat1, flat2,
            TestDuplicates.IMAGE_CACHE, TestDuplicates.HASH_THRESHOLD
        )
        self.assertTrue(
            score >= TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS
        )

    def test_different_prices(self):
        """
        Two flats with different prices should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["cost"] += 1000

        score = duplicates.get_duplicate_score(
            flat1, flat2,
            TestDuplicates.IMAGE_CACHE, TestDuplicates.HASH_THRESHOLD
        )
        self.assertTrue(
            score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS
        )

    def test_different_rooms(self):
        """
        Two flats with different rooms quantity should not be detected as
        duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["rooms"] += 1

        score = duplicates.get_duplicate_score(
            flat1, flat2,
            TestDuplicates.IMAGE_CACHE, TestDuplicates.HASH_THRESHOLD
        )
        self.assertTrue(
            score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS
        )

    def test_different_areas(self):
        """
        Two flats with different areas should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["area"] += 10

        score = duplicates.get_duplicate_score(
            flat1, flat2,
            TestDuplicates.IMAGE_CACHE, TestDuplicates.HASH_THRESHOLD
        )
        self.assertTrue(
            score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS
        )

    def test_different_areas_decimals(self):
        """
        Two flats which areas integers are equal but decimals are present and
        different should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat1["area"] = 50.65
        flat2["area"] = 50.37

        score = duplicates.get_duplicate_score(
            flat1, flat2,
            TestDuplicates.IMAGE_CACHE, TestDuplicates.HASH_THRESHOLD
        )
        self.assertTrue(
            score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS
        )

    def test_different_phones(self):
        """
        Two flats with different phone numbers should not be detected as
        duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["phone"] = "0708091011"

        score = duplicates.get_duplicate_score(
            flat1, flat2,
            TestDuplicates.IMAGE_CACHE, TestDuplicates.HASH_THRESHOLD
        )
        self.assertTrue(
            score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS
        )

    def test_real_duplicates(self):
        """
        Two flats with same price, area and rooms quantity should be detected
        as duplicates.
        """
        flats = self.load_files(
            "127028739@seloger",
            "14428129@explorimmo"
        )

        score = duplicates.get_duplicate_score(
            flats[0], flats[1],
            TestDuplicates.IMAGE_CACHE, TestDuplicates.HASH_THRESHOLD
        )
        self.assertTrue(
            score >= TestDuplicates.DUPLICATES_MIN_SCORE_WITH_PHOTOS
        )


def run():
    """
    Run all the tests
    """
    LOGGER.info("Running tests…")
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestTexts)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        assert result.wasSuccessful()

        suite = unittest.TestLoader().loadTestsFromTestCase(TestPhoneNumbers)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        assert result.wasSuccessful()

        suite = unittest.TestLoader().loadTestsFromTestCase(TestDuplicates)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        assert result.wasSuccessful()

        suite = unittest.TestLoader().loadTestsFromTestCase(TestPhotos)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        assert result.wasSuccessful()
    except AssertionError:
        sys.exit(1)
