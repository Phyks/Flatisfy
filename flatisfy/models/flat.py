# coding: utf-8
"""
This modules defines an SQLAlchemy ORM model for a flat.
"""
# pylint: disable=locally-disabled,invalid-name,too-few-public-methods
from __future__ import absolute_import, print_function, unicode_literals

import enum
import logging

import arrow

from sqlalchemy import (
    Column, DateTime, Enum, Float, SmallInteger, String, Text
)

from flatisfy.database.base import BASE
from flatisfy.database.types import MagicJSON


LOGGER = logging.getLogger(__name__)


class FlatUtilities(enum.Enum):
    """
    An enum of the possible utilities status for a flat entry.
    """
    included = 10
    unknown = 0
    excluded = -10


class FlatStatus(enum.Enum):
    """
    An enum of the possible status for a flat entry.
    """
    user_deleted = -100
    duplicate = -20
    ignored = -10
    new = 0
    followed = 10
    contacted = 20
    answer_no = 30
    answer_yes = 31


# List of statuses that are automatically handled, and which the user cannot
# manually set through the UI.
AUTOMATED_STATUSES = [
    FlatStatus.new,
    FlatStatus.duplicate,
    FlatStatus.ignored
]


class Flat(BASE):
    """
    SQLAlchemy ORM model to store a flat.
    """
    __tablename__ = "flats"
    __searchable__ = ["title", "text", "station", "location", "details"]

    # Weboob data
    id = Column(String, primary_key=True)
    area = Column(Float)
    bedrooms = Column(Float)
    cost = Column(Float)
    currency = Column(String)
    utilities = Column(Enum(FlatUtilities), default=FlatUtilities.unknown)
    date = Column(DateTime)
    details = Column(MagicJSON)
    location = Column(String)
    phone = Column(String)
    photos = Column(MagicJSON)
    rooms = Column(Float)
    station = Column(String)
    text = Column(Text)
    title = Column(String)
    urls = Column(MagicJSON)
    merged_ids = Column(MagicJSON)
    notes = Column(Text)
    notation = Column(SmallInteger, default=0)

    # Flatisfy data
    # TODO: Should be in another table with relationships
    flatisfy_stations = Column(MagicJSON)
    flatisfy_postal_code = Column(String)
    flatisfy_time_to = Column(MagicJSON)
    flatisfy_constraint = Column(String)

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
        if "flatisfy" in flat_dict:
            flat_dict["flatisfy_stations"] = (
                flat_dict["flatisfy"].get("matched_stations", [])
            )
            flat_dict["flatisfy_postal_code"] = (
                flat_dict["flatisfy"].get("postal_code", None)
            )
            flat_dict["flatisfy_time_to"] = (
                flat_dict["flatisfy"].get("time_to", {})
            )
            flat_dict["flatisfy_constraint"] = (
                flat_dict["flatisfy"].get("constraint", "default")
            )
            del flat_dict["flatisfy"]

        # Handle utilities field
        if not isinstance(flat_dict["utilities"], FlatUtilities):
            if flat_dict["utilities"] == "C.C.":
                flat_dict["utilities"] = FlatUtilities.included
            elif flat_dict["utilities"] == "H.C.":
                flat_dict["utilities"] = FlatUtilities.excluded
            else:
                flat_dict["utilities"] = FlatUtilities.unknown

        # Handle status field
        flat_status = flat_dict.get("status", "new")
        if not isinstance(flat_status, FlatStatus):
            try:
                flat_dict["status"] = getattr(FlatStatus, flat_status)
            except AttributeError:
                if "status" in flat_dict:
                    del flat_dict["status"]
                LOGGER.warn("Unkown flat status %s, ignoring it.",
                            flat_status)

        # Handle date field
        flat_dict["date"] = arrow.get(flat_dict["date"]).naive

        flat_object = Flat()
        flat_object.__dict__.update(flat_dict)
        return flat_object

    def __repr__(self):
        return "<Flat(id=%s, urls=%s)>" % (self.id, self.urls)


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
        if isinstance(flat_repr["status"], FlatStatus):
            flat_repr["status"] = flat_repr["status"].name
        if isinstance(flat_repr["utilities"], FlatUtilities):
            flat_repr["utilities"] = flat_repr["utilities"].name

        return flat_repr
