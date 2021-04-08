# -*- coding: utf-8 -*-

# Copyright(C) 2014      Bezleputh
#
# This file is part of a woob module.
#
# This woob module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This woob module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this woob module. If not, see <http://www.gnu.org/licenses/>.

from woob.tools.test import BackendTest
from woob.tools.value import Value
from woob.capabilities.housing import Query, POSTS_TYPES, ADVERT_TYPES
from woob.tools.capabilities.housing.housing_test import HousingTest


class LeboncoinTest(BackendTest, HousingTest):
    MODULE = 'leboncoin'

    FIELDS_ALL_HOUSINGS_LIST = [
        "id", "type", "advert_type", "url", "title",
        "currency", "utilities", "date", "location", "text"
    ]
    FIELDS_ANY_HOUSINGS_LIST = [
        "area",
        "cost",
        "price_per_meter",
        "photos"
    ]
    FIELDS_ALL_SINGLE_HOUSING = [
        "id", "url", "type", "advert_type", "house_type", "title",
        "cost", "currency", "utilities", "date", "location", "text",
        "rooms", "details"
    ]
    FIELDS_ANY_SINGLE_HOUSING = [
        "area",
        "GES",
        "DPE",
        "photos",
        # Don't test phone as leboncoin API is strongly rate-limited
    ]

    def setUp(self):
        if not self.is_backend_configured():
            self.backend.config['advert_type'] = Value(value='a')
            self.backend.config['region'] = Value(value='ile_de_france')

    def test_leboncoin_rent(self):
        query = Query()
        query.area_min = 20
        query.cost_max = 1500
        query.type = POSTS_TYPES.RENT
        query.cities = []
        for city in self.backend.search_city('paris'):
            city.backend = self.backend.name
            query.cities.append(city)
            if len(query.cities) == 3:
                break
        self.check_against_query(query)

    def test_leboncoin_sale(self):
        query = Query()
        query.area_min = 20
        query.type = POSTS_TYPES.SALE
        query.cities = []
        for city in self.backend.search_city('paris'):
            city.backend = self.backend.name
            query.cities.append(city)
            if len(query.cities) == 3:
                break
        self.check_against_query(query)

    def test_leboncoin_furnished_rent(self):
        query = Query()
        query.area_min = 20
        query.cost_max = 1500
        query.type = POSTS_TYPES.FURNISHED_RENT
        query.cities = []
        for city in self.backend.search_city('paris'):
            city.backend = self.backend.name
            query.cities.append(city)
            if len(query.cities) == 3:
                break
        self.check_against_query(query)

    def test_leboncoin_professional(self):
        query = Query()
        query.area_min = 20
        query.cost_max = 900
        query.type = POSTS_TYPES.RENT
        query.advert_types = [ADVERT_TYPES.PROFESSIONAL]
        query.cities = []
        for city in self.backend.search_city('paris'):
            city.backend = self.backend.name
            query.cities.append(city)
        self.check_against_query(query)
