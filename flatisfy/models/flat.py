# coding: utf-8
"""
This modules defines an SQLAlchemy ORM model for a flat.
"""
# pylint: disable=invalid-name,too-few-public-methods
from __future__ import absolute_import, print_function, unicode_literals

import enum

from sqlalchemy import Column, DateTime, Enum, Float, String, Text

from flatisfy.database.base import BASE
from flatisfy.database.types import MagicJSON


class FlatStatus(enum.Enum):
    """
    An enum of the possible status for a flat entry.
    """
    purged = -10
    new = 0
    contacted = 10
    answer_no = 20
    answer_yes = 21


class Flat(BASE):
    """
    SQLAlchemy ORM model to store a flat.
    """
    __tablename__ = "flats"

    # Weboob data
    id = Column(String, primary_key=True)
    area = Column(Float)
    bedrooms = Column(Float)
    cost = Column(Float)
    currency = Column(String)
    date = Column(DateTime)
    details = Column(MagicJSON)
    location = Column(String)
    phone = Column(String)
    photos = Column(MagicJSON)
    rooms = Column(Float)
    station = Column(String)
    text = Column(Text)
    title = Column(String)
    url = Column(String)

    # Flatisfy data
    # TODO: Should be in another table with relationships
    flatisfy_stations = Column(MagicJSON)
    flatisfy_postal_code = Column(String)
    flatisfy_time_to = Column(MagicJSON)

    # Status
    status = Column(Enum(FlatStatus), default=FlatStatus.new)

    @staticmethod
    def from_dict(flat_dict):
        """
        Create a Flat object from a flat dict as manipulated by the filtering
        pass.
        """
        # Handle flatisfy metadata
        flat_dict = flat_dict.copy()
        flat_dict["flatisfy_stations"] = (
            flat_dict["flatisfy"].get("matched_stations", None)
        )
        flat_dict["flatisfy_postal_code"] = (
            flat_dict["flatisfy"].get("postal_code", None)
        )
        flat_dict["flatisfy_time_to"] = (
            flat_dict["flatisfy"].get("time_to", None)
        )
        del flat_dict["flatisfy"]

        # Handle date field
        flat_dict["date"] = None  # TODO

        flat_object = Flat()
        flat_object.__dict__.update(flat_dict)
        return flat_object

    def __repr__(self):
        return "<Flat(id=%s, url=%s)>" % (self.id, self.url)


    def json_api_repr(self):
        """
        Return a dict representation of this flat object that is JSON
        serializable.
        """
        flat_repr = {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_")
        }
        flat_repr["status"] = str(flat_repr["status"])

        return flat_repr
