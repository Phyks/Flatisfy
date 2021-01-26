# coding: utf-8
"""
This modules defines an SQLAlchemy ORM model for public transport opendata.
"""
# pylint: disable=locally-disabled,invalid-name,too-few-public-methods
from __future__ import absolute_import, print_function, unicode_literals

import logging

from sqlalchemy import Column, Float, Integer, String

from flatisfy.database.base import BASE


LOGGER = logging.getLogger(__name__)


class PublicTransport(BASE):
    """
    SQLAlchemy ORM model to store public transport opendata.
    """

    __tablename__ = "public_transports"

    id = Column(Integer, primary_key=True)
    # Area is an identifier to prevent loading unnecessary stops. For now it is
    # following ISO 3166-2.
    area = Column(String, index=True)
    name = Column(String)
    lat = Column(Float)
    lng = Column(Float)

    def __repr__(self):
        return "<PublicTransport(id=%s)>" % self.id
