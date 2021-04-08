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
from __future__ import unicode_literals
from decimal import Decimal

from woob.tools.date import parse_french_date
from woob.browser.pages import HTMLPage, JsonPage, pagination
from woob.browser.elements import ItemElement, ListElement, DictElement, method
from woob.browser.filters.standard import (CleanText, CleanDecimal, Regexp,
                                             Env, BrowserURL, Format, Currency)
from woob.browser.filters.html import Attr, Link, XPath, CleanHTML
from woob.browser.filters.json import Dict
from woob.capabilities.base import NotAvailable, NotLoaded
from woob.capabilities.housing import (Housing, City, HousingPhoto,
                                         UTILITIES, ENERGY_CLASS, POSTS_TYPES,
                                         ADVERT_TYPES, HOUSE_TYPES)
from woob.tools.capabilities.housing.housing import PricePerMeterFilter


class CitiesPage(JsonPage):
    @method
    class iter_cities(DictElement):

        class item(ItemElement):
            klass = City

            obj_id = Dict('id')
            obj_name = Dict('name')


class HousingPage(HTMLPage):
    @pagination
    @method
    class iter_housings(ListElement):
        item_xpath = '//div[has-class("search-list-item-alt")]'

        def next_page(self):
            return Link('//ul[@class="pagination"]/li[@class="next"]/a')(self)

        class item(ItemElement):
            klass = Housing

            def condition(self):
                title = self.obj_title(self)
                isNotFurnishedOk = True
                if self.env['query_type'] == POSTS_TYPES.RENT:
                    isNotFurnishedOk = 'meublé' not in title.lower()
                return (
                    Regexp(Link('./div/a[has-class("item-title")]'), '/annonces/(.*)', default=None)(self) and
                    isNotFurnishedOk
                )

            def parse(self, el):
                rooms_bedrooms_area = el.xpath(
                    './div/a[has-class("item-title")]/ul[has-class("item-tags")]/li'
                )
                self.env['rooms'] = NotLoaded
                self.env['bedrooms'] = NotLoaded
                self.env['area'] = NotLoaded

                for item in rooms_bedrooms_area:
                    name = CleanText('.')(item)
                    if 'chambre' in name.lower():
                        name = 'bedrooms'
                        value = CleanDecimal('.')(item)
                    elif 'pièce' in name.lower():
                        name = 'rooms'
                        value = CleanDecimal('.')(item)
                    else:
                        name = 'area'
                        value = CleanDecimal(
                            Regexp(
                                CleanText(
                                    '.'
                                ),
                                r'(\d*\.*\d*) .*'
                            )
                        )(item)
                    self.env[name] = value

            obj_id = Regexp(Link('./div/a[has-class("item-title")]'), '/annonces/(.*)')
            obj_type = Env('query_type')
            obj_advert_type = ADVERT_TYPES.PERSONAL

            def obj_house_type(self):
                item_link = Link('./div/a[@class="item-title"]')(self)
                house_type = item_link.split('/')[-1].split('-')[0]
                if 'parking' in house_type:
                    return HOUSE_TYPES.PARKING
                elif 'appartement' in house_type:
                    return HOUSE_TYPES.APART
                elif 'terrain' in house_type:
                    return HOUSE_TYPES.LAND
                elif 'maison' in house_type:
                    return HOUSE_TYPES.HOUSE
                else:
                    return HOUSE_TYPES.OTHER

            obj_title = CleanText('./div/a[has-class("item-title")]')
            obj_area = Env('area')
            obj_cost = CleanDecimal(CleanText('./div/a[has-class("item-title")]/span[@class="item-price"]'),
                                    replace_dots=True, default=Decimal(0))
            obj_currency = Currency(
                './div/a[@class="item-title"]/span[@class="item-price"]'
            )
            obj_utilities = UTILITIES.UNKNOWN

            obj_station = CleanText('./div/p[@class="item-transports"]', default=NotLoaded)

            def obj_location(self):
                return CleanText('./div/p[@class="item-description"]')(self).split(".")[0]

            obj_text = CleanText('./div/p[@class="item-description"]', replace=[(' Lire la suite', '')])
            obj_rooms = Env('rooms')
            obj_bedrooms = Env('bedrooms')
            obj_price_per_meter = PricePerMeterFilter()

            obj_url = Format(
                u'http://www.pap.fr%s',
                Link('./div/a[@class="item-title"]')
            )

            def obj_photos(self):
                photos = []
                for img in XPath('./a/img/@src')(self):
                    if(
                            img.endswith("visuel-nophoto.png") or
                            img.endswith('miniature-video.png')
                    ):
                        continue
                    photos.append(HousingPhoto(u'%s' % img))
                return photos

    @method
    class get_housing(ItemElement):
        klass = Housing

        def parse(self, el):
            rooms_bedrooms_area = el.xpath(
                './/ul[has-class("item-tags")]/li'
            )
            self.env['rooms'] = NotAvailable
            self.env['bedrooms'] = NotAvailable
            self.env['area'] = NotAvailable

            for item in rooms_bedrooms_area:
                name = CleanText('.')(item)
                if 'chambre' in name.lower():
                    name = 'bedrooms'
                    value = CleanDecimal('./strong')(item)
                elif 'pièce' in name.lower():
                    name = 'rooms'
                    value = CleanDecimal('./strong')(item)
                elif ' m²' in name and 'le m²' not in name:
                    name = 'area'
                    value = CleanDecimal(
                        Regexp(
                            CleanText(
                                '.'
                            ),
                            r'(\d*\.*\d*) .*'
                        )
                    )(item)
                self.env[name] = value

        obj_id = Env('_id')

        def obj_type(self):
            prev_link = Link('//ol[has-class("breadcrumb")]/li[1]/a')(self)
            if 'location' in prev_link:
                title = self.obj_title(self)
                if 'meublé' in title.lower():
                    return POSTS_TYPES.FURNISHED_RENT
                else:
                    return POSTS_TYPES.RENT
            elif 'vente' in prev_link:
                return POSTS_TYPES.SALE
            elif 'viager' in prev_link:
                return POSTS_TYPES.VIAGER
            else:
                return NotAvailable
        obj_advert_type = ADVERT_TYPES.PERSONAL

        def obj_house_type(self):
            prev_link = Link('//ol[has-class("breadcrumb")]/li[1]/a')(self)
            house_type = prev_link.split('-')[-1]
            if 'parking' in house_type:
                return HOUSE_TYPES.PARKING
            elif 'appartement' in house_type:
                return HOUSE_TYPES.APART
            elif 'terrain' in house_type:
                return HOUSE_TYPES.LAND
            elif 'maison' in house_type:
                return HOUSE_TYPES.HOUSE
            else:
                return HOUSE_TYPES.OTHER

        obj_title = CleanText(
            '//h1[@class="item-title"]'
        )
        obj_cost = CleanDecimal(
            '//h1[@class="item-title"]/span[@class="item-price"]',
            replace_dots=True
        )
        obj_currency = Currency(
            '//h1[@class="item-title"]/span[@class="item-price"]'
        )
        obj_utilities = UTILITIES.UNKNOWN
        obj_area = Env('area')

        def obj_date(self):
            date = CleanText(
                '//p[@class="item-date"]'
            )(self).split("/")[-1].strip()
            return parse_french_date(date)

        obj_rooms = Env('rooms')
        obj_bedrooms = Env('bedrooms')
        obj_price_per_meter = PricePerMeterFilter()
        obj_location = CleanText('//div[has-class("item-description")]/h2')
        obj_text = CleanText(CleanHTML('//div[has-class("item-description")]/div/p'))

        def obj_station(self):
            return ", ".join([
                station.text
                for station in XPath(
                    '//ul[has-class("item-transports")]//span[has-class("label")]'
                )(self)
            ])

        def obj_phone(self):
            phone = CleanText('(//div[has-class("contact-proprietaire-box")]//strong[@class="tel-wrapper"])[1]')(self)
            phone = phone.replace(' ', ', ')
            return phone

        obj_url = BrowserURL('housing', _id=Env('_id'))

        def obj_DPE(self):
            DPE = Attr(
                '//div[has-class("energy-box")]//div[has-class("energy-rank")]',
                'class',
                default=""
            )(self)
            if DPE:
                DPE = [x.replace("energy-rank-", "").upper()
                       for x in DPE.split() if x.startswith("energy-rank-")][0]
            return getattr(ENERGY_CLASS, DPE, NotAvailable)

        def obj_photos(self):
            photos = []
            for img in XPath('//div[@class="owl-thumbs"]/a/img/@src')(self):
                if not img.endswith('miniature-video.png'):
                    photos.append(HousingPhoto(u'%s' % img))
            return photos
