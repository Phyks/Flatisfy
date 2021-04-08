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

from __future__ import unicode_literals

from woob.browser.pages import HTMLPage, JsonPage
from woob.browser.elements import ItemElement, ListElement, DictElement, method
from woob.browser.filters.json import Dict
from woob.browser.filters.standard import (Currency, Format, CleanText,
                                             Regexp, CleanDecimal, Date, Env,
                                             BrowserURL)
from woob.browser.filters.html import Attr, XPath, CleanHTML
from woob.capabilities.housing import (Housing, HousingPhoto, City,
                                         UTILITIES, ENERGY_CLASS, POSTS_TYPES,
                                         ADVERT_TYPES, HOUSE_TYPES)
from woob.capabilities.base import NotAvailable, NotLoaded
from woob.tools.capabilities.housing.housing import PricePerMeterFilter
from woob.tools.compat import urljoin


class CitiesPage(JsonPage):
    @method
    class get_cities(DictElement):
        item_xpath = '*/children'

        class item(ItemElement):
            klass = City

            def condition(self):
                return Dict('lct_parent_id')(self) != '0'

            obj_id = Format('%s_%s', Dict('lct_id'), Dict('lct_level'))
            obj_name = Format('%s %s', Dict('lct_name'), Dict('lct_post_code'))


class PhonePage(HTMLPage):
    def get_phone(self):
        return CleanText('//div[has-class("phone")]', children=False)(self.doc)


class HousingPage(HTMLPage):
    @method
    class get_housing(ItemElement):
        klass = Housing

        obj_id = Env('_id')

        def obj_type(self):
            url = BrowserURL('housing', _id=Env('_id'))(self)
            if 'colocation' in url:
                return POSTS_TYPES.SHARING
            elif 'location' in url:
                isFurnished = False
                for li in XPath('//ul[@itemprop="description"]/li')(self):
                    label = CleanText('./span[has-class("criteria-label")]')(li)
                    if label.lower() == "meublé":
                        isFurnished = (
                            CleanText('./span[has-class("criteria-value")]')(li).lower() == 'oui'
                        )
                if isFurnished:
                    return POSTS_TYPES.FURNISHED_RENT
                else:
                    return POSTS_TYPES.RENT
            elif 'vente' in url:
                return POSTS_TYPES.SALE
            return NotAvailable
        obj_advert_type = ADVERT_TYPES.PROFESSIONAL

        def obj_house_type(self):
            house_type = CleanText('.//h2[@class="offerMainFeatures"]/div')(self).lower()
            if house_type == "appartement":
                return HOUSE_TYPES.APART
            elif house_type == "maison":
                return HOUSE_TYPES.HOUSE
            elif house_type == "terrain":
                return HOUSE_TYPES.LAND
            elif house_type == "parking":
                return HOUSE_TYPES.PARKING
            else:
                return HOUSE_TYPES.OTHER

        obj_title = Attr('//meta[@property="og:title"]', 'content')
        obj_area = CleanDecimal(
            CleanText(
                '//p[@class="offerArea"]/span',
            ),
            default=NotAvailable
        )
        obj_rooms = CleanDecimal(
                        Regexp(
                            CleanText('//p[@class="offerRooms"]/span'),
                            '(\d) p.',
                            default=NotAvailable
                        ),
                        default=NotAvailable
                    )
        obj_bedrooms = CleanDecimal(
                        Regexp(
                            CleanText('//p[@class="offerRooms"]/span'),
                            '(\d) ch.',
                            default=NotAvailable
                        ),
                        default=NotAvailable
                    )
        obj_cost = CleanDecimal('//*[@itemprop="price"]', default=0)
        obj_currency = Currency(
            '//*[@itemprop="price"]'
        )

        def obj_utilities(self):
            notes = CleanText('//p[@class="offer-description-notes"]')(self)
            if "Loyer mensuel charges comprises" in notes:
                return UTILITIES.INCLUDED
            else:
                return UTILITIES.UNKNOWN

        obj_price_per_meter = PricePerMeterFilter()
        obj_date = Date(Regexp(CleanText('//div[@class="offer-description-notes"]'),
                               u'.* Mis à jour: (\d{2}/\d{2}/\d{4}).*'),
                        dayfirst=True)
        obj_text = CleanHTML('//p[@class="descrProperty"]')
        obj_location = CleanText('//em[@class="infoAdresse"]')
        obj_station = CleanText(
            '//div[has-class("offer-description-metro")]',
            default=NotAvailable
        )

        obj_url = BrowserURL('housing', _id=Env('_id'))

        def obj_photos(self):
            photos = []
            for img in XPath('//ul[@class="thumbsContainer"]//img/@src')(self):
                if img.endswith('.svg'):
                    continue
                url = u'%s' % img.replace('182x136', '800x600')
                url = urljoin(self.page.url, url)  # Ensure URL is absolute
                photos.append(HousingPhoto(url))
            return photos

        def obj_DPE(self):
            energy_value = CleanText(
                '//ul[@class="energyInfosDPE"]//li[@class="energyInfos"]/span/@data-class',
                default=""
            )(self)
            if len(energy_value):
                energy_value = energy_value.replace("DPE", "").strip()[0]
            return getattr(ENERGY_CLASS, energy_value, NotAvailable)

        def obj_GES(self):
            greenhouse_value = CleanText(
                '//ul[@class="energyInfosGES"]//li[@class="energyInfos"]/span/@data-class',
                default=""
            )(self)
            if len(greenhouse_value):
                greenhouse_value = greenhouse_value.replace("GES", "").strip()[0]
            return getattr(ENERGY_CLASS, greenhouse_value, NotAvailable)

        def obj_details(self):
            details = {}

            details["creationDate"] = Date(
                Regexp(
                    CleanText(
                        '//div[@class="offer-description-notes"]'
                    ),
                    u'.*Mis en ligne: (\d{2}/\d{2}/\d{4}).*'
                ),
                dayfirst=True
            )(self)

            honoraires = CleanText(
                (
                    '//div[has-class("offer-price")]/span[has-class("lbl-agencyfees")]'
                ),
                default=None
            )(self)
            if honoraires:
                details["Honoraires"] = (
                    "{} (TTC, en sus)".format(
                        honoraires.split(":")[1].strip()
                    )
                )

            for li in XPath('//ul[@itemprop="description"]/li')(self):
                label = CleanText('./span[has-class("criteria-label")]')(li)
                value = CleanText('./span[has-class("criteria-value")]')(li)
                details[label] = value

            return details

    def get_phone_url_datas(self):
        a = XPath('//button[has-class("js-show-phone-offer-sale-bottom")]')(self.doc)[0]
        urlcontact = 'http://www.logic-immo.com/modalMail'
        params = {}
        params['universe'] = CleanText('./@data-univers')(a)
        params['source'] = CleanText('./@data-source')(a)
        params['pushcontact'] = CleanText('./@data-pushcontact')(a)
        params['mapper'] = CleanText('./@data-mapper')(a)
        params['offerid'] = CleanText('./@data-offerid')(a)
        params['offerflag'] = CleanText('./@data-offerflag')(a)
        params['campaign'] = CleanText('./@data-campaign')(a)
        params['xtpage'] = CleanText('./@data-xtpage')(a)
        params['offertransactiontype'] = CleanText('./@data-offertransactiontype')(a)
        params['aeisource'] = CleanText('./@data-aeisource')(a)
        params['shownumber'] = CleanText('./@data-shownumber')(a)
        params['corail'] = 1
        return urlcontact, params


class SearchPage(HTMLPage):
    @method
    class iter_sharing(ListElement):
        item_xpath = '//article[has-class("offer-block")]'

        class item(ItemElement):
            klass = Housing

            obj_id = Format('colocation-%s', CleanText('./div/header/@id', replace=[('header-offer-', '')]))
            obj_type = POSTS_TYPES.SHARING
            obj_advert_type = ADVERT_TYPES.PROFESSIONAL
            obj_title = CleanText(CleanHTML('./div/header/section/p[@class="property-type"]/span/@title'))

            obj_area = CleanDecimal('./div/header/section/p[@class="offer-attributes"]/a/span[@class="offer-area-number"]',
                                    default=0)

            obj_cost = CleanDecimal('./div/header/section/p[@class="price"]', default=0)
            obj_currency = Currency(
                './div/header/section/p[@class="price"]'
            )
            obj_utilities = UTILITIES.UNKNOWN

            obj_text = CleanText(
                './div/div[@class="content-offer"]/section[has-class("content-desc")]/p/span[has-class("offer-text")]/@title',
                default=NotLoaded
            )

            obj_date = Date(Regexp(CleanText('./div/header/section/p[has-class("update-date")]'),
                                   ".*(\d{2}/\d{2}/\d{4}).*"))

            obj_location = CleanText(
                '(./div/div[@class="content-offer"]/section[has-class("content-desc")]/p)[1]/span/@title',
                default=NotLoaded
            )

    @method
    class iter_housings(ListElement):
        item_xpath = '//div[has-class("offer-list")]//div[has-class("offer-block")]'

        class item(ItemElement):
            offer_details_wrapper = (
                './/div[has-class("offer-details-wrapper")]'
            )
            klass = Housing

            obj_id = Format(
                '%s-%s',
                Regexp(Env('type'), '(.*)-.*'),
                CleanText('./@id', replace=[('header-offer-', '')])
            )
            obj_type = Env('query_type')
            obj_advert_type = ADVERT_TYPES.PROFESSIONAL

            def obj_house_type(self):
                house_type = CleanText('.//div[has-class("offer-details-caracteristik")]/meta[@itemprop="name"]/@content')(self).lower()
                if house_type == "appartement":
                    return HOUSE_TYPES.APART
                elif house_type == "maison":
                    return HOUSE_TYPES.HOUSE
                elif house_type == "terrain":
                    return HOUSE_TYPES.LAND
                elif house_type == "parking":
                    return HOUSE_TYPES.PARKING
                else:
                    return HOUSE_TYPES.OTHER

            obj_title = CleanText('.//div[has-class("offer-details-type")]/a/@title')

            obj_url = Format(u'%s%s',
                             CleanText('.//div/a[@class="offer-link"]/@href'),
                             CleanText('.//div/a[@class="offer-link"]/\
@data-orpi', default=""))

            obj_area = CleanDecimal(
                (
                    offer_details_wrapper +
                    '/div/div/div[has-class("offer-details-second")]' +
                    '/div/h3[has-class("offer-attributes")]/span' +
                    '/span[has-class("offer-area-number")]'
                ),
                default=NotLoaded
            )
            obj_rooms = CleanDecimal(
                (
                    offer_details_wrapper +
                    '/div/div/div[has-class("offer-details-second")]' +
                    '/div/h3[has-class("offer-attributes")]' +
                    '/span[has-class("offer-rooms")]' +
                    '/span[has-class("offer-rooms-number")]'
                ),
                default=NotAvailable
            )
            obj_cost = CleanDecimal(
                Regexp(
                    CleanText(
                        (
                            offer_details_wrapper +
                            '/div/p[@class="offer-price"]/span'
                        ),
                        default=NotLoaded
                    ),
                    '(.*) [%s%s%s]' % (u'€', u'$', u'£'),
                    default=NotLoaded
                ),
                default=NotLoaded
            )
            obj_currency = Currency(
                offer_details_wrapper + '/div/p[has-class("offer-price")]/span'
            )
            obj_price_per_meter = PricePerMeterFilter()
            obj_utilities = UTILITIES.UNKNOWN
            obj_text = CleanText(
                offer_details_wrapper + '/div/div/div/p[has-class("offer-description")]/span'
            )
            obj_location = CleanText(
                offer_details_wrapper + '/div[@class="offer-details-location"]',
                replace=[('Voir sur la carte','')]
            )

            def obj_photos(self):
                photos = []
                url = None
                try:
                    url = Attr(
                        './/div[has-class("offer-picture")]//img',
                        'src'
                    )(self)
                except:
                    pass

                if url:
                    url = url.replace('335x253', '800x600')
                    url = urljoin(self.page.url, url)  # Ensure URL is absolute
                    photos.append(HousingPhoto(url))
                return photos

            def obj_details(self):
                details = {}
                honoraires = CleanText(
                    (
                        self.offer_details_wrapper +
                        '/div/div/p[@class="offer-agency-fees"]'
                    ),
                    default=None
                )(self)
                if honoraires:
                    details["Honoraires"] = (
                        "{} (TTC, en sus)".format(
                            honoraires.split(":")[1].strip()
                        )
                    )
                return details
