# coding: utf-8
"""
This module contains the definition of the web app API routes.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import json

import bottle

import flatisfy.data
from flatisfy.models import flat as flat_model

# TODO: Flat post-processing code should be factorized


def index_v1():
    """
    API v1 index route:

        GET /api/v1/
    """
    return {
        "flats": "/api/v1/flats",
        "flat": "/api/v1/flat/:id",
        "search": "/api/v1/search",
        "time_to_places": "/api/v1/time_to/places"
    }


def flats_v1(config, db):
    """
    API v1 flats route:

        GET /api/v1/flats

    :return: The available flats objects in a JSON ``data`` dict.
    """
    postal_codes = flatisfy.data.load_data("postal_codes", config)

    flats = [
        flat.json_api_repr()
        for flat in db.query(flat_model.Flat).all()
    ]

    for flat in flats:
        if flat["flatisfy_postal_code"]:
            postal_code_data = postal_codes[flat["flatisfy_postal_code"]]
            flat["flatisfy_postal_code"] = {
                "postal_code": flat["flatisfy_postal_code"],
                "name": postal_code_data["nom"],
                "gps": postal_code_data["gps"]
            }
        else:
            flat["flatisfy_postal_code"] = {}

    return {
        "data": flats
    }


def flats_by_status_v1(status, db):
    """
    API v1 flats route with a specific status:

        GET /api/v1/flats/status/:status

    :return: The matching flats objects in a JSON ``data`` dict.
    """
    try:
        flats = [
            flat.json_api_repr()
            for flat in (
                db.query(flat_model.Flat)
                .filter_by(status=getattr(flat_model.FlatStatus, status))
                .all()
            )
        ]
    except AttributeError:
        return bottle.HTTPError(400, "Invalid status provided.")

    return {
        "data": flats
    }


def flat_v1(flat_id, config, db):
    """
    API v1 flat route:

        GET /api/v1/flat/:flat_id

    :return: The flat object in a JSON ``data`` dict.
    """
    postal_codes = flatisfy.data.load_data("postal_codes", config)

    flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()

    if not flat:
        return bottle.HTTPError(404, "No flat with id {}.".format(flat_id))

    flat = flat.json_api_repr()

    if flat["flatisfy_postal_code"]:
        postal_code_data = postal_codes[flat["flatisfy_postal_code"]]
        flat["flatisfy_postal_code"] = {
            "postal_code": flat["flatisfy_postal_code"],
            "name": postal_code_data["nom"],
            "gps": postal_code_data["gps"]
        }
    else:
        flat["flatisfy_postal_code"] = {}

    return {
        "data": flat
    }


def update_flat_status_v1(flat_id, db):
    """
    API v1 route to update flat status:

        POST /api/v1/flat/:flat_id/status
        Data: {
            "status": "NEW_STATUS"
        }

    :return: The new flat object in a JSON ``data`` dict.
    """
    flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
    if not flat:
        return bottle.HTTPError(404, "No flat with id {}.".format(flat_id))

    try:
        flat.status = getattr(
            flat_model.FlatStatus, json.load(bottle.request.body)["status"]
        )
    except (AttributeError, ValueError, KeyError):
        return bottle.HTTPError(400, "Invalid status provided.")

    json_flat = flat.json_api_repr()

    return {
        "data": json_flat
    }


def update_flat_notes_v1(flat_id, db):
    """
    API v1 route to update flat notes:

        POST /api/v1/flat/:flat_id/notes
        Data: {
            "notes": "NEW_NOTES"
        }

    :return: The new flat object in a JSON ``data`` dict.
    """
    flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
    if not flat:
        return bottle.HTTPError(404, "No flat with id {}.".format(flat_id))

    try:
        flat.notes = json.load(bottle.request.body)["notes"]
    except (ValueError, KeyError):
        return bottle.HTTPError(400, "Invalid notes provided.")

    json_flat = flat.json_api_repr()

    return {
        "data": json_flat
    }


def update_flat_notation_v1(flat_id, db):
    """
    API v1 route to update flat notation:

        POST /api/v1/flat/:flat_id/notation
        Data: {
            "notation": "NEW_NOTATION"
        }

    :return: The new flat object in a JSON ``data`` dict.
    """
    flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
    if not flat:
        return bottle.HTTPError(404, "No flat with id {}.".format(flat_id))

    try:
        flat.notation = json.load(bottle.request.body)["notation"]
        assert flat.notes >= 0 and flat.notes <= 5
    except (AssertionError, ValueError, KeyError):
        return bottle.HTTPError(400, "Invalid notation provided.")

    json_flat = flat.json_api_repr()

    return {
        "data": json_flat
    }


def time_to_places_v1(config):
    """
    API v1 route to fetch the details of the places to compute time to.

        GET /api/v1/time_to/places

    :return: The JSON dump of the places to compute time to (dict of places
    names mapped to GPS coordinates).
    """
    places = {
        k: v["gps"]
        for k, v in config["constraints"]["time_to"].items()
    }
    return {
        "data": places
    }


def search_v1(config):
    """
    API v1 route to perform a fulltext search on flats.

        POST /api/v1/search
        Data: {
            "query": "SOME_QUERY"
        }

    :return: The matching flat objects in a JSON ``data`` dict.
    """
    postal_codes = flatisfy.data.load_data("postal_codes", config)

    try:
        query = json.load(bottle.request.body)["query"]
    except (ValueError, KeyError):
        return bottle.HTTPError(400, "Invalid query provided.")

    flats_db_query = flat_model.Flat.search_query(query)
    flats = [
        flat.json_api_repr()
        for flat in flats_db_query
    ]

    for flat in flats:
        if flat["flatisfy_postal_code"]:
            postal_code_data = postal_codes[flat["flatisfy_postal_code"]]
            flat["flatisfy_postal_code"] = {
                "postal_code": flat["flatisfy_postal_code"],
                "name": postal_code_data["nom"],
                "gps": postal_code_data["gps"]
            }
        else:
            flat["flatisfy_postal_code"] = {}

    return {
        "data": flats
    }
