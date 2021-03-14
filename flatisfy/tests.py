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
import tempfile

from io import BytesIO

import PIL
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
                return PIL.Image.open(BytesIO(requests.get(url).content))


class TestTexts(unittest.TestCase):
    """
    Checks string normalizations.
    """

    def test_roman_numbers(self):
        """
        Checks roman numbers replacement.
        """
        self.assertEqual("XIV", tools.convert_arabic_to_roman("14"))

        self.assertEqual("XXXIX", tools.convert_arabic_to_roman("39"))

        self.assertEqual("40", tools.convert_arabic_to_roman("40"))

        self.assertEqual("1987", tools.convert_arabic_to_roman("1987"))

        self.assertEqual(
            "Dans le XVe arrondissement",
            tools.convert_arabic_to_roman_in_text("Dans le 15e arrondissement"),
        )

        self.assertEqual("XXeme arr.", tools.convert_arabic_to_roman_in_text("20eme arr."))

        self.assertEqual(
            "A AIX EN PROVENCE",
            tools.convert_arabic_to_roman_in_text("A AIX EN PROVENCE"),
        )

        self.assertEqual(
            "Montigny Le Bretonneux",
            tools.convert_arabic_to_roman_in_text("Montigny Le Bretonneux"),
        )

    def test_roman_numbers_in_text(self):
        """
        Checks conversion of roman numbers to arabic ones in string
        normalization.
        """
        self.assertEqual(
            "dans le XVe arrondissement",
            tools.normalize_string("Dans le 15e arrondissement"),
        )

        self.assertEqual("paris XVe, 75005", tools.normalize_string("Paris 15e, 75005"))

        self.assertEqual("paris xve, 75005", tools.normalize_string("Paris XVe, 75005"))

    def test_multiple_whitespaces(self):
        """
        Checks whitespaces are collapsed.
        """
        self.assertEqual("avec ascenseur", tools.normalize_string("avec   ascenseur"))

    def test_whitespace_trim(self):
        """
        Checks that trailing and beginning whitespaces are trimmed.
        """
        self.assertEqual("rennes 35000", tools.normalize_string("  Rennes 35000 "))

    def test_accents(self):
        """
        Checks accents are replaced.
        """
        self.assertEqual("eeeaui", tools.normalize_string(u"éèêàüï"))


class TestPhoneNumbers(unittest.TestCase):
    """
    Checks phone numbers normalizations.
    """

    def test_prefix(self):
        """
        Checks phone numbers with international prefixes.
        """
        self.assertEqual("0605040302", duplicates.homogeneize_phone_number("+33605040302"))

    def test_dots_separators(self):
        """
        Checks phone numbers with dots.
        """
        self.assertEqual("0605040302", duplicates.homogeneize_phone_number("06.05.04.03.02"))

    def test_spaces_separators(self):
        """
        Checks phone numbers with spaces.
        """
        self.assertEqual("0605040302", duplicates.homogeneize_phone_number("06 05 04 03 02"))


class TestPhotos(unittest.TestCase):
    HASH_THRESHOLD = 10  # pylint: disable=invalid-name

    def __init__(self, *args, **kwargs):
        self.IMAGE_CACHE = LocalImageCache(  # pylint: disable=invalid-name
            storage_dir=tempfile.mkdtemp(prefix="flatisfy-")
        )
        super(TestPhotos, self).__init__(*args, **kwargs)

    def test_same_photo_twice(self):
        """
        Compares a photo against itself.
        """
        photo = {"url": TESTS_DATA_DIR + "127028739@seloger.jpg"}

        self.assertTrue(duplicates.compare_photos(photo, photo, self.IMAGE_CACHE, self.HASH_THRESHOLD))

    def test_different_photos(self):
        """
        Compares two different photos.
        """
        self.assertFalse(
            duplicates.compare_photos(
                {"url": TESTS_DATA_DIR + "127028739@seloger.jpg"},
                {"url": TESTS_DATA_DIR + "127028739-2@seloger.jpg"},
                self.IMAGE_CACHE,
                self.HASH_THRESHOLD,
            )
        )

        self.assertFalse(
            duplicates.compare_photos(
                {"url": TESTS_DATA_DIR + "127028739-2@seloger.jpg"},
                {"url": TESTS_DATA_DIR + "127028739-3@seloger.jpg"},
                self.IMAGE_CACHE,
                self.HASH_THRESHOLD,
            )
        )

    def test_matching_photos(self):
        """
        Compares two matching photos with different size and source.
        """
        self.assertTrue(
            duplicates.compare_photos(
                {"url": TESTS_DATA_DIR + "127028739@seloger.jpg"},
                {"url": TESTS_DATA_DIR + "14428129@explorimmo.jpg"},
                self.IMAGE_CACHE,
                self.HASH_THRESHOLD,
            )
        )

        self.assertTrue(
            duplicates.compare_photos(
                {"url": TESTS_DATA_DIR + "127028739-2@seloger.jpg"},
                {"url": TESTS_DATA_DIR + "14428129-2@explorimmo.jpg"},
                self.IMAGE_CACHE,
                self.HASH_THRESHOLD,
            )
        )

        self.assertTrue(
            duplicates.compare_photos(
                {"url": TESTS_DATA_DIR + "127028739-3@seloger.jpg"},
                {"url": TESTS_DATA_DIR + "14428129-3@explorimmo.jpg"},
                self.IMAGE_CACHE,
                self.HASH_THRESHOLD,
            )
        )

        self.assertTrue(
            duplicates.compare_photos(
                {"url": TESTS_DATA_DIR + "127028739@seloger.jpg"},
                {"url": TESTS_DATA_DIR + "127028739-watermark@seloger.jpg"},
                self.IMAGE_CACHE,
                self.HASH_THRESHOLD,
            )
        )

    def test_matching_cropped_photos(self):
        """
        Compares two matching photos with one being cropped.
        """
        # Fixme: the image hash treshold should be 10 ideally
        self.assertTrue(
            duplicates.compare_photos(
                {"url": TESTS_DATA_DIR + "vertical.jpg"},
                {"url": TESTS_DATA_DIR + "vertical-cropped.jpg"},
                self.IMAGE_CACHE,
                20,
            )
        )

        # Fixme: the image hash treshold should be 10 ideally
        self.assertTrue(
            duplicates.compare_photos(
                {"url": TESTS_DATA_DIR + "13783671@explorimmo.jpg"},
                {"url": TESTS_DATA_DIR + "124910113@seloger.jpg"},
                self.IMAGE_CACHE,
                20,
            )
        )


class TestImageCache(unittest.TestCase):
    """
    Checks image cache is working as expected.
    """

    def __init__(self, *args, **kwargs):
        self.IMAGE_CACHE = ImageCache(storage_dir=tempfile.mkdtemp(prefix="flatisfy-"))  # pylint: disable=invalid-name
        super(TestImageCache, self).__init__(*args, **kwargs)

    def test_invalid_url(self):
        """
        Check that it returns nothing on an invalid URL.
        """
        # See https://framagit.org/phyks/Flatisfy/issues/116.
        self.assertIsNone(self.IMAGE_CACHE.get("https://httpbin.org/status/404"))
        self.assertIsNone(self.IMAGE_CACHE.get("https://httpbin.org/status/500"))

    def test_invalid_data(self):
        """
        Check that it returns nothing on an invalid data.
        """
        # See https://framagit.org/phyks/Flatisfy/issues/116.
        self.assertIsNone(self.IMAGE_CACHE.get("https://httpbin.org/"))


class TestDuplicates(unittest.TestCase):
    """
    Checks duplicates detection.
    """

    DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS = 8  # pylint: disable=invalid-name
    DUPLICATES_MIN_SCORE_WITH_PHOTOS = 15  # pylint: disable=invalid-name
    HASH_THRESHOLD = 10  # pylint: disable=invalid-name

    def __init__(self, *args, **kwargs):
        self.IMAGE_CACHE = LocalImageCache(  # pylint: disable=invalid-name
            storage_dir=tempfile.mkdtemp(prefix="flatisfy-")
        )
        super(TestDuplicates, self).__init__(*args, **kwargs)

    @staticmethod
    def generate_fake_flat():
        """
        Generates a fake flat post.
        """
        backend = BACKENDS_BY_PRECEDENCE[random.randint(0, len(BACKENDS_BY_PRECEDENCE) - 1)]
        return {
            "id": str(random.randint(100000, 199999)) + "@" + backend,
            "phone": "0607080910",
            "rooms": random.randint(1, 4),
            "utilities": "",
            "area": random.randint(200, 1500) / 10,
            "cost": random.randint(100000, 300000),
            "bedrooms": random.randint(1, 4),
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
        score = duplicates.get_duplicate_score(flat1, flat2, self.IMAGE_CACHE, self.HASH_THRESHOLD)
        self.assertGreaterEqual(score, self.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_prices(self):
        """
        Two flats with different prices should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["cost"] += 1000

        score = duplicates.get_duplicate_score(flat1, flat2, self.IMAGE_CACHE, self.HASH_THRESHOLD)
        self.assertLess(score, self.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_rooms(self):
        """
        Two flats with different rooms quantity should not be detected as
        duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["rooms"] += 1

        score = duplicates.get_duplicate_score(flat1, flat2, self.IMAGE_CACHE, self.HASH_THRESHOLD)
        self.assertLess(score, self.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_areas(self):
        """
        Two flats with different areas should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["area"] += 10

        score = duplicates.get_duplicate_score(flat1, flat2, self.IMAGE_CACHE, self.HASH_THRESHOLD)
        self.assertLess(score, self.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_areas_decimals(self):
        """
        Two flats which areas integers are equal but decimals are present and
        different should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat1["area"] = 50.65
        flat2["area"] = 50.37

        score = duplicates.get_duplicate_score(flat1, flat2, self.IMAGE_CACHE, self.HASH_THRESHOLD)
        self.assertLess(score, self.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_phones(self):
        """
        Two flats with different phone numbers should not be detected as
        duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["phone"] = "0708091011"

        score = duplicates.get_duplicate_score(flat1, flat2, self.IMAGE_CACHE, self.HASH_THRESHOLD)
        self.assertLess(score, self.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_real_duplicates(self):
        """
        Two flats with same price, area and rooms quantity should be detected
        as duplicates.
        """
        flats = self.load_files("127028739@seloger", "14428129@explorimmo")

        score = duplicates.get_duplicate_score(flats[0], flats[1], self.IMAGE_CACHE, self.HASH_THRESHOLD)
        self.assertGreaterEqual(score, self.DUPLICATES_MIN_SCORE_WITH_PHOTOS)

        # TODO: fixme, find new testing examples
        # flats = self.load_files(
        #     "128358415@seloger",
        #     "14818297@explorimmo"
        # )

        # score = duplicates.get_duplicate_score(
        #     flats[0], flats[1],
        #     self.IMAGE_CACHE, 20
        # )
        # self.assertGreaterEqual(score, self.DUPLICATES_MIN_SCORE_WITH_PHOTOS)

        # # Different number of photos, and some are cropped
        # flats = self.load_files(
        #     "124910113@seloger",
        #     "13783671@explorimmo"
        # )

        # score = duplicates.get_duplicate_score(
        #     flats[0], flats[1],
        #     self.IMAGE_CACHE, 20
        # )
        # self.assertGreaterEqual(score, self.DUPLICATES_MIN_SCORE_WITH_PHOTOS)

        # # Same flat, different agencies, texts and photos
        # flats = self.load_files(
        #     "122509451@seloger",
        #     "127963747@seloger"
        # )

        # score = duplicates.get_duplicate_score(
        #     flats[0], flats[1],
        #     self.IMAGE_CACHE, self.HASH_THRESHOLD
        # )
        # # Fix me : should be TestDuplicates.DUPLICATES_MIN_SCORE_WITH_PHOTOS
        # self.assertGreaterEqual(score, 4)

        # # Really similar flats, but different
        # flats = self.load_files(
        #     "123312807@seloger",
        #     "123314207@seloger"
        # )

        # score = duplicates.get_duplicate_score(
        #     flats[0], flats[1],
        #     self.IMAGE_CACHE, self.HASH_THRESHOLD
        # )
        # self.assertLess(score, self.DUPLICATES_MIN_SCORE_WITH_PHOTOS)


def run():
    """
    Run all the tests
    """
    LOGGER.info("Running tests…")
    try:
        for testsuite in [
            TestTexts,
            TestPhoneNumbers,
            TestImageCache,
            TestDuplicates,
            TestPhotos,
        ]:
            suite = unittest.TestLoader().loadTestsFromTestCase(testsuite)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            assert result.wasSuccessful()
    except AssertionError:
        sys.exit(1)
