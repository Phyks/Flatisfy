# -*- coding: utf-8 -*-

# Copyright(C) 2012 Romain Bignon
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


from woob.browser.pages import JsonPage, pagination, HTMLPage
from woob.browser.elements import ItemElement, DictElement, method
from woob.browser.filters.json import Dict
from woob.browser.filters.html import XPath
from woob.browser.filters.standard import (CleanText, CleanDecimal, Currency,
                                             Env, Regexp, Field, BrowserURL)
from woob.capabilities.base import NotAvailable, NotLoaded
from woob.capabilities.housing import (Housing, HousingPhoto, City,
                                         UTILITIES, ENERGY_CLASS, POSTS_TYPES,
                                         ADVERT_TYPES)
from woob.capabilities.address import PostalAddress
from woob.tools.capabilities.housing.housing import PricePerMeterFilter
from woob.tools.json import json
from woob.exceptions import ActionNeeded
from .constants import TYPES, RET
import codecs
import decimal


class ErrorPage(HTMLPage):
    def on_load(self):
        raise ActionNeeded("Please resolve the captcha")


class CitiesPage(JsonPage):
    @method
    class iter_cities(DictElement):
        ignore_duplicate = True

        class item(ItemElement):
            klass = City

            obj_id = Dict('Params/ci')
            obj_name = Dict('Display')


class SearchResultsPage(HTMLPage):
    def __init__(self, *args, **kwargs):
        HTMLPage.__init__(self, *args, **kwargs)
        json_content = Regexp(CleanText('//script'),
                              r"window\[\"initialData\"\] = JSON.parse\(\"({.*})\"\);window\[\"tags\"\]")(self.doc)
        json_content = codecs.unicode_escape_decode(json_content)[0]
        json_content = json_content.encode('utf-8', 'surrogatepass').decode('utf-8')
        self.doc = json.loads(json_content)

    @pagination
    @method
    class iter_housings(DictElement):
        item_xpath = 'cards/list'
        # Prevent DataError on same ids
        ignore_duplicate = True

        def next_page(self):
            page_nb = Dict('navigation/pagination/page')(self)
            max_results = Dict('navigation/counts/count')(self)
            results_per_page = Dict('navigation/pagination/resultsPerPage')(self)

            if int(max_results) / int(results_per_page) > int(page_nb):
                return BrowserURL('search', query=Env('query'), page_number=int(page_nb) + 1)(self)

        # TODO handle bellesdemeures

        class item(ItemElement):
            klass = Housing

            def condition(self):
                return (
                    Dict('cardType')(self) not in ['advertising', 'ali', 'localExpert']
                    and Dict('id', default=False)(self)
                    and Dict('classifiedURL', default=False)(self)
                )

            obj_id = Dict('id')

            def obj_type(self):
                idType = int(Env('query_type')(self))
                type = next(k for k, v in TYPES.items() if v == idType)
                if type == POSTS_TYPES.FURNISHED_RENT:
                    # SeLoger does not let us discriminate between furnished and not furnished.
                    return POSTS_TYPES.RENT
                return type

            def obj_title(self):
                return "{} - {} - {}".format(Dict('estateType')(self),
                                             " / ".join(Dict('tags')(self)),
                                             Field('location')(self))

            def obj_advert_type(self):
                is_agency = Dict('contact/agencyId', default=False)(self)
                if is_agency:
                    return ADVERT_TYPES.PROFESSIONAL
                else:
                    return ADVERT_TYPES.PERSONAL

            obj_utilities = UTILITIES.EXCLUDED

            def obj_photos(self):
                photos = []
                for photo in Dict('photos')(self):
                    photos.append(HousingPhoto(photo))
                return photos

            def obj_location(self):
                quartier = Dict('districtLabel')(self)
                quartier = quartier if quartier else ''
                ville = Dict('cityLabel')(self)
                ville = ville if ville else ''
                cp = Dict('zipCode')(self)
                cp = cp if cp else ''
                return u'%s %s (%s)' % (quartier, ville, cp)

            obj_url = Dict('classifiedURL')

            obj_text = Dict('description')

            obj_cost = CleanDecimal(Dict('pricing/price', default=NotLoaded), default=NotLoaded)
            obj_currency = Currency(Dict('pricing/price', default=NotLoaded), default=NotLoaded)
            obj_price_per_meter = CleanDecimal(Dict('pricing/squareMeterPrice'), default=PricePerMeterFilter)


class HousingPage(HTMLPage):
    def __init__(self, *args, **kwargs):
        HTMLPage.__init__(self, *args, **kwargs)
        json_content = Regexp(
            CleanText('//script'),
            r"window\[\"initialData\"\] = JSON.parse\(\"({.*})\"\);"
        )(self.doc)
        json_content = codecs.unicode_escape_decode(json_content)[0]
        json_content = json_content.encode('utf-8', 'surrogatepass').decode('utf-8')
        self.doc = {
            "advert": json.loads(json_content).get('advert', {}).get('mainAdvert', {}),
            "agency": json.loads(json_content).get('agency', {})
        }

    @method
    class get_housing(ItemElement):
        klass = Housing

        def parse(self, el):
            self.agency_doc = el['agency']
            self.el = el['advert']

        obj_id = Dict('id')

        def obj_house_type(self):
            naturebien = Dict('propertyNatureId')(self)
            try:
                return next(k for k, v in RET.items() if v == naturebien)
            except StopIteration:
                return NotLoaded

        def obj_type(self):
            idType = Dict('idTransactionType')(self)
            try:
                type = next(k for k, v in TYPES.items() if v == idType)
                if type == POSTS_TYPES.FURNISHED_RENT:
                    # SeLoger does not let us discriminate between furnished and not furnished.
                    return POSTS_TYPES.RENT
                return type
            except StopIteration:
                return NotAvailable

        def obj_advert_type(self):
            if 'Agences' in self.agency_doc['type']:
                return ADVERT_TYPES.PROFESSIONAL
            else:
                return ADVERT_TYPES.PERSONAL

        def obj_photos(self):
            photos = []

            for photo in Dict('photoList')(self):
                photos.append(HousingPhoto(photo['fullscreenUrl']))

            return photos

        obj_title = Dict('title')

        def obj_location(self):
            address = Dict('address')(self)
            return u'%s %s (%s)' % (address['neighbourhood'], address['city'],
                                   address['zipCode'])

        def obj_address(self):
            address = Dict('address')(self)
            p = PostalAddress()
            p.street = address['street']
            p.postal_code = address['zipCode']
            p.city = address['city']
            p.full_address = Field('location')(self)
            return p

        obj_text = Dict('description')

        def obj_cost(self):
            propertyPrice = Dict('propertyPrice')(self)
            return decimal.Decimal(propertyPrice['prix'])
        def obj_currency(self):
            propertyPrice = Dict('propertyPrice')(self)
            return propertyPrice['priceUnit']

        obj_price_per_meter = PricePerMeterFilter()

        obj_area = CleanDecimal(Dict('surface'))
        def obj_url(self):
            return self.page.url
        def obj_phone(self):
            return self.agency_doc.get('agencyPhoneNumber', {}).get('value',
                                                                    NotAvailable)

        def obj_utilities(self):
            return NotLoaded  # TODO

        obj_bedrooms = CleanDecimal(Dict('bedroomCount'))
        obj_rooms = CleanDecimal(Dict('numberOfRooms'))


class HousingJsonPage(JsonPage):
    @method
    class get_housing(ItemElement):
        klass = Housing

        def obj_DPE(self):
            DPE = Dict("energie", default="")(self)
            if DPE['status'] > 0:
                return NotAvailable
            else:
                return getattr(ENERGY_CLASS, DPE['lettre'], NotAvailable)

        def obj_GES(self):
            GES = Dict("ges", default="")(self)
            if GES['status'] > 0:
                return NotAvailable
            else:
                return getattr(ENERGY_CLASS, GES['lettre'], NotAvailable)

        def obj_details(self):
            details = {}

            for c in Dict('categories')(self):
                if c['criteria']:
                    details[c['name']] = ' / '.join([_['value'] for _ in c['criteria']])

            for _, c in Dict('infos_acquereur')(self).items():
                for key, value in c.items():
                    details[key] = value

            return details
