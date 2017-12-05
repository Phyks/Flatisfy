# coding: utf-8
"""
This module contains the definition of the web app API routes.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import datetime
import json
import re

import bottle
import vobject

import flatisfy.data
from flatisfy.models import flat as flat_model
from flatisfy.models.postal_code import PostalCode


def JSONError(error_code, error_str):
    bottle.response.status = error_code
    bottle.response.content_type = "application/json"
    return json.dumps(dict(error=error_str, status_code=error_code))


def _serialize_flat(flat, config):
    """
    Serialize a flat for JSON API.

    Converts it to a JSON-representable dict and add postal code metadata.

    :param flat: An SQLAlchemy Flat object.
    :param config: A config dict.
    :returns: A flat dict ready to be serialized.
    """
    flat = flat.json_api_repr()

    postal_codes = {}
    for constraint_name, constraint in config["constraints"].items():
        postal_codes[constraint_name] = flatisfy.data.load_data(
            PostalCode, constraint, config
        )

    try:
        assert flat["flatisfy_postal_code"]

        postal_code_data = next(
            x
            for x in postal_codes.get(flat["flatisfy_constraint"], [])
            if x.postal_code == flat["flatisfy_postal_code"]
        )
        flat["flatisfy_postal_code"] = {
            "postal_code": flat["flatisfy_postal_code"],
            "name": postal_code_data.name,
            "gps": (postal_code_data.lat, postal_code_data.lng)
        }
    except (AssertionError, StopIteration):
        flat["flatisfy_postal_code"] = {}

    return flat


def index_v1():
    """
    API v1 index route:

        GET /api/v1/
    """
    return {
        "flats": "/api/v1/flats",
        "flat": "/api/v1/flat/:id",
        "search": "/api/v1/search",
        "ics": "/api/v1/ics/visits.ics",
        "time_to_places": "/api/v1/time_to_places"
    }


def flats_v1(config, db):
    """
    API v1 flats route:

        GET /api/v1/flats

    .. note:: Filtering can be done through the ``filter`` GET param, according
    to JSON API spec (http://jsonapi.org/recommendations/#filtering).

    :return: The available flats objects in a JSON ``data`` dict.
    """
    try:
        db_query = db.query(flat_model.Flat)

        # Handle filtering according to JSON API spec
        FILTER_RE = re.compile(r"filter\[([A-z0-9_]+)\]")
        filters = {}
        for param in bottle.request.query:
            filter_match = FILTER_RE.match(param)
            if not filter:
                continue
            field = filter_match.group(1)
            value = bottle.request.query[filter_match.group(0)]
            filters[field] = value
        db_query = db_query.filter_by(**filters)

        # Build flat list
        flats = [
            _serialize_flat(flat, config)
            for flat in db_query
        ]
        return {
            "data": flats
        }
    except Exception as exc:
        return JSONError(500, str(exc))


def flat_v1(flat_id, config, db):
    """
    API v1 flat route:

        GET /api/v1/flats/:flat_id

    :return: The flat object in a JSON ``data`` dict.
    """
    try:
        flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()

        if not flat:
            return JSONError(404, "No flat with id {}.".format(flat_id))

        return {
            "data": _serialize_flat(flat, config)
        }
    except Exception as exc:
        return JSONError(500, str(exc))


def update_flat_v1(flat_id, config, db):
    """
    API v1 route to update flat status:

        PATCH /api/v1/flat/:flat_id
        Data: {
            "status": "NEW_STATUS",
            "visit_date": "ISO8601 DATETIME"
        }

    .. note:: The keys in the data sent are same keys as in ``Flat`` model. You
    can provide any subset of them to update part of the flat infos.

    :return: The new flat object in a JSON ``data`` dict.
    """
    try:
        flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
        if not flat:
            return JSONError(404, "No flat with id {}.".format(flat_id))

        try:
            json_body = json.load(bottle.request.body)
            for k, v in json_body.items():
                setattr(flat, k, v)
        except ValueError as exc:
            return JSONError(
                400,
                "Invalid payload provided: {}.".format(str(exc))
            )

        return {
            "data": _serialize_flat(flat, config)
        }
    except Exception as exc:
        return JSONError(500, str(exc))


def time_to_places_v1(config):
    """
    API v1 route to fetch the details of the places to compute time to.

        GET /api/v1/time_to_places

    :return: The JSON dump of the places to compute time to (dict of places
    names mapped to GPS coordinates).
    """
    try:
        places = {}
        for constraint_name, constraint in config["constraints"].items():
            places[constraint_name] = {
                k: v["gps"]
                for k, v in constraint["time_to"].items()
            }
        return {
            "data": places
        }
    except Exception as exc:
        return JSONError(500, str(exc))


def search_v1(db, config):
    """
    API v1 route to perform a fulltext search on flats.

        POST /api/v1/search
        Data: {
            "query": "SOME_QUERY"
        }

    :return: The matching flat objects in a JSON ``data`` dict.
    """
    try:
        try:
            query = json.load(bottle.request.body)["query"]
        except (ValueError, KeyError):
            return JSONError(400, "Invalid query provided.")

        flats_db_query = flat_model.Flat.search_query(db, query)
        flats = [
            _serialize_flat(flat, config)
            for flat in flats_db_query
        ]

        return {
            "data": flats
        }
    except Exception as exc:
        return JSONError(500, str(exc))


def ics_feed_v1(config, db):
    """
    API v1 ICS feed of visits route:

        GET /api/v1/ics/visits.ics

    :return: The ICS feed for the visits.
    """
    cal = vobject.iCalendar()
    try:
        flats_with_visits = db.query(flat_model.Flat).filter(
            flat_model.Flat.visit_date.isnot(None)
        )

        for flat in flats_with_visits:
            vevent = cal.add('vevent')
            vevent.add('dtstart').value = flat.visit_date
            vevent.add('dtend').value = (
                flat.visit_date + datetime.timedelta(hours=1)
            )
            vevent.add('summary').value = 'Visit - {}'.format(flat.title)

            description = (
                '{} (area: {}, cost: {} {})\n{}#/flat/{}\n'.format(
                    flat.title, flat.area, flat.cost, flat.currency,
                    config['website_url'], flat.id
                )
            )
            description += '\n{}\n'.format(flat.text)
            if flat.notes:
                description += '\n{}\n'.format(flat.notes)

            vevent.add('description').value = description
    except:
        pass

    return cal.serialize()
