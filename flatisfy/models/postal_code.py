# coding: utf-8
"""
This modules defines an SQLAlchemy ORM model for a postal code opendata.
"""
# pylint: disable=locally-disabled,invalid-name,too-few-public-methods
from __future__ import absolute_import, print_function, unicode_literals

import logging

from sqlalchemy import Column, Float, Integer, String, UniqueConstraint

from flatisfy.database.base import BASE


LOGGER = logging.getLogger(__name__)


class PostalCode(BASE):
    """
    SQLAlchemy ORM model to store a postal code opendata.
    """

    __tablename__ = "postal_codes"

    id = Column(Integer, primary_key=True)
    # Area is an identifier to prevent loading unnecessary stops. For now it is
    # following ISO 3166-2.
    area = Column(String, index=True)
    postal_code = Column(String, index=True)
    name = Column(String, index=True)
    lat = Column(Float)
    lng = Column(Float)
    UniqueConstraint("postal_code", "name")

    def __repr__(self):
        return "<PostalCode(id=%s)>" % self.id

    def json_api_repr(self):
        """
        Return a dict representation of this postal code object that is JSON
        serializable.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
