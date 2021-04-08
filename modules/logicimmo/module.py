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


from woob.tools.backend import Module
from woob.capabilities.housing import (CapHousing, Housing, HousingPhoto,
                                         ADVERT_TYPES)
from woob.capabilities.base import UserError
from .browser import LogicimmoBrowser


__all__ = ['LogicimmoModule']


class LogicImmoCitiesError(UserError):
    """
    Raised when more than 3 cities are selected
    """
    def __init__(self, msg='You cannot select more than three cities'):
        UserError.__init__(self, msg)


class LogicimmoModule(Module, CapHousing):
    NAME = 'logicimmo'
    DESCRIPTION = u'logicimmo website'
    MAINTAINER = u'Bezleputh'
    EMAIL = 'carton_ben@yahoo.fr'
    LICENSE = 'AGPLv3+'
    VERSION = '2.1'

    BROWSER = LogicimmoBrowser

    def get_housing(self, housing):
        if isinstance(housing, Housing):
            id = housing.id
        else:
            id = housing
            housing = None
        housing = self.browser.get_housing(id, housing)
        return housing

    def search_city(self, pattern):
        return self.browser.get_cities(pattern)

    def search_housings(self, query):
        if(len(query.advert_types) == 1 and
           query.advert_types[0] == ADVERT_TYPES.PERSONAL):
            # Logic-immo is pro only
            return list()

        cities_names = ['%s' % c.name.replace(' ', '-') for c in query.cities if c.backend == self.name]
        cities_ids = ['%s' % c.id for c in query.cities if c.backend == self.name]

        if len(cities_names) == 0:
            return list()

        if len(cities_names) > 3:
            raise LogicImmoCitiesError()

        cities = ','.join(cities_names + cities_ids)
        return self.browser.search_housings(query.type, cities.lower(), query.nb_rooms,
                                            query.area_min, query.area_max,
                                            query.cost_min, query.cost_max,
                                            query.house_types)

    def fill_housing(self, housing, fields):
        if 'phone' in fields:
            housing.phone = self.browser.get_phone(housing.id)
            fields.remove('phone')

        if len(fields) > 0:
            self.browser.get_housing(housing.id, housing)

        return housing

    def fill_photo(self, photo, fields):
        if 'data' in fields and photo.url and not photo.data:
            photo.data = self.browser.open(photo.url).content
        return photo

    OBJECTS = {Housing: fill_housing,
               HousingPhoto: fill_photo,
               }
