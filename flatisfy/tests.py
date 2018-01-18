# coding: utf-8
"""
This module contains unit testing functions.
"""

import random
import logging
import unittest
import copy
import os
import json
from flatisfy import tools
from flatisfy.filters import duplicates
from flatisfy.filters.cache import ImageCache
from flatisfy.constants import BACKENDS_BY_PRECEDENCE

LOGGER = logging.getLogger(__name__)
TESTS_DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/test_files/"

class TestTexts(unittest.TestCase):
    def test_roman_numbers(self):
        """
        Checks roman numbers replacement.
        """
        tester = tools.RomanNumbers()
        self.assertTrue(tester.check_valid("XIV"))
        self.assertTrue(not tester.check_valid("ABC"))

        self.assertEqual(
            "14",
            tester.convert_to_arabic("XIV")
        )

        self.assertEqual(
            "1987",
            tester.convert_to_arabic("MCMLXXXVII")
        )

        self.assertEqual(
            "Dans le 15e arrondissement",
            tester.convert_to_arabic_in_text("Dans le XVe arrondissement")
        )

        self.assertEqual(
            "20eme arr.",
            tester.convert_to_arabic_in_text("XXeme arr.")
        )

        self.assertEqual(
            "A AIX EN PROVENCE",
            tester.convert_to_arabic_in_text("A AIX EN PROVENCE")
        )

    def test_roman_numbers_in_text(self):
        self.assertEqual(
            "dans le 15e arrondissement",
            tools.normalize_string("Dans le XVe arrondissement")
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

class TestDuplicates(unittest.TestCase):
    DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS = 14
    DUPLICATES_MIN_SCORE_WITH_PHOTOS = 15
    IMAGE_CACHE = ImageCache()

    def generate_fake_flat(self):
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
            "bedrooms": random.randint(1, 4)
        }

    def load_files(self, file1, file2):
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
        score = duplicates.get_duplicate_score(flat1, flat2, TestDuplicates.IMAGE_CACHE)
        self.assertTrue(score >= TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_prices(self):
        """
        Two flats with different prices should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["cost"] += 1000

        score = duplicates.get_duplicate_score(flat1, flat2, TestDuplicates.IMAGE_CACHE)
        self.assertTrue(score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_rooms(self):
        """
        Two flats with different rooms quantity should not be detected as
        duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["rooms"] += 1

        score = duplicates.get_duplicate_score(flat1, flat2, TestDuplicates.IMAGE_CACHE)
        self.assertTrue(score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_areas(self):
        """
        Two flats with different areas should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["area"] += 10

        score = duplicates.get_duplicate_score(flat1, flat2, TestDuplicates.IMAGE_CACHE)
        self.assertTrue(score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_areas_decimals(self):
        """
        Two flats which areas integers are equal but decimals are present and
        different should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat1["area"] = 50.65
        flat2["area"] = 50.37

        score = duplicates.get_duplicate_score(flat1, flat2, TestDuplicates.IMAGE_CACHE)
        self.assertTrue(score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_different_phones(self):
        """
        Two flats with different phone numbers should not be detected as duplicates.
        """
        flat1 = self.generate_fake_flat()
        flat2 = copy.deepcopy(flat1)
        flat2["phone"] = "0708091011"

        score = duplicates.get_duplicate_score(flat1, flat2, TestDuplicates.IMAGE_CACHE)
        self.assertTrue(score < TestDuplicates.DUPLICATES_MIN_SCORE_WITHOUT_PHOTOS)

    def test_real_duplicates(self):
        """
        Two flats with same price, area and rooms quantity should be detected as
        duplicates.
        """
        flats = self.load_files(
            "127028739@seloger",
            "14428129@explorimmo"
        )

        score = duplicates.get_duplicate_score(flats[0], flats[1], TestDuplicates.IMAGE_CACHE)
        self.assertTrue(score >= TestDuplicates.DUPLICATES_MIN_SCORE_WITH_PHOTOS)

def run(config):
    """
    Run all the tests

    :param config: A config dict.
    """
    LOGGER.info("Running tests…")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTexts)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhoneNumbers)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestDuplicates)
    unittest.TextTestRunner(verbosity=2).run(suite)
