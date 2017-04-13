# coding: utf-8
"""
This module contains the definition of the web app API routes.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

from flatisfy.models import flat as flat_model


def index_v1():
    """
    API v1 index route:

        GET /api/v1/
    """
    return {
        "flats": "/api/v1/flats"
    }


def flats_v1(db):
    """
    API v1 flats route:

        GET /api/v1/flats
    """
    flats = [
        flat.json_api_repr()
        for flat in db.query(flat_model.Flat).all()
    ]
    return {
        "data": flats
    }


def flat_v1(flat_id, db):
    """
    API v1 flat route:

        GET /api/v1/flat/:flat_id
    """
    flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
    return {
        "data": flat.json_api_repr()
    }
