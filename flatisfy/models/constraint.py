# coding: utf-8
"""
This modules defines an SQLAlchemy ORM model for a search constraint.
"""
# pylint: disable=locally-disabled,invalid-name,too-few-public-methods
from __future__ import absolute_import, print_function, unicode_literals

import logging
from sqlalchemy import (
    Column, Float, Integer, String
)
from sqlalchemy_utils.types.json import JSONType
from sqlalchemy_utils.types.scalar_list import ScalarListType

import enum
from sqlalchemy_enum_list import EnumListType

from flatisfy.database.base import BASE


LOGGER = logging.getLogger(__name__)


class HouseTypes(enum.Enum):
    """
    An enum of the possible house types.
    """
    APART = 0
    HOUSE = 1
    PARKING = 2
    LAND = 3
    OTHER = 4
    UNKNOWN = 5


class PostTypes(enum.Enum):
    """
    An enum of the possible posts types.
    """
    RENT = 0
    SALE = 1
    SHARING = 2


class Constraint(BASE):
    """
    SQLAlchemy ORM model to store a search constraint.
    """
    __tablename__ = "constraints"

    id = Column(String, primary_key=True)
    name = Column(String)
    type = Column(EnumListType(PostTypes, int))
    house_types = Column(EnumListType(HouseTypes, int))
    postal_codes = Column(ScalarListType())  # TODO
    area_min = Column(Float, default=None)  # in m^2
    area_max = Column(Float, default=None)  # in m^2
    cost_min = Column(Float, default=None)  # in currency unit
    cost_max = Column(Float, default=None)  # in currency unit
    rooms_min = Column(Integer, default=None)
    rooms_max = Column(Integer, default=None)
    bedrooms_min = Column(Integer, default=None)
    bedrooms_max = Column(Integer, default=None)
    minimum_nb_photos = Column(Integer, default=None)
    description_should_contain = Column(ScalarListType())  # list of terms
    time_to = Column(JSONType)  # TODO

    def __repr__(self):
        return "<Constraint(id=%s, name=%s)>" % (self.id, self.name)

    def json_api_repr(self):
        """
        Return a dict representation of this constraint object that is JSON
        serializable.
        """
        constraint_repr = {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_")
        }

        return constraint_repr
