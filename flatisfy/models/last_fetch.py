# coding: utf-8
"""
This modules defines an SQLAlchemy ORM model for a flat.
"""
# pylint: disable=locally-disabled,invalid-name,too-few-public-methods
from __future__ import absolute_import, print_function, unicode_literals

import logging

from sqlalchemy import (
    Column,
    DateTime,
    String,
)

from flatisfy.database.base import BASE


LOGGER = logging.getLogger(__name__)


class LastFetch(BASE):
    """
    SQLAlchemy ORM model to store last timestamp of fetch by backend.
    """

    __tablename__ = "last_fetch"

    backend = Column(String, primary_key=True)
    last_fetch = Column(DateTime)
    constraint_name = Column(String)
