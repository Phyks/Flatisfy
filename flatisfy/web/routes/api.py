# coding: utf-8
"""
This module contains the definition of the web app API routes.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import datetime
import json

import arrow
import bottle
import vobject

import flatisfy.data
from flatisfy.models import flat as flat_model
from flatisfy.models.postal_code import PostalCode


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
        "time_to_places": "/api/v1/time_to/places"
    }


def flats_v1(config, db):
    """
    API v1 flats route:

        GET /api/v1/flats

    :return: The available flats objects in a JSON ``data`` dict.
    """
    try:
        flats = [
            _serialize_flat(flat, config)
            for flat in db.query(flat_model.Flat).all()
        ]

        return {
            "data": flats
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def flats_by_status_v1(status, config, db):
    """
    API v1 flats route with a specific status:

        GET /api/v1/flats/status/:status

    :return: The matching flats objects in a JSON ``data`` dict.
    """
    try:
        flats = [
            _serialize_flat(flat, config)
            for flat in (
                db.query(flat_model.Flat)
                .filter_by(status=getattr(flat_model.FlatStatus, status))
                .all()
            )
        ]

        return {
            "data": flats
        }
    except AttributeError:
        return bottle.HTTPError(400, "Invalid status provided.")
    except Exception as e:
        return {
            "error": str(e)
        }


def flat_v1(flat_id, config, db):
    """
    API v1 flat route:

        GET /api/v1/flat/:flat_id

    :return: The flat object in a JSON ``data`` dict.
    """
    try:
        flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()

        if not flat:
            return bottle.HTTPError(404, "No flat with id {}.".format(flat_id))

        return {
            "data": _serialize_flat(flat, config)
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def update_flat_status_v1(flat_id, config, db):
    """
    API v1 route to update flat status:

        POST /api/v1/flat/:flat_id/status
        Data: {
            "status": "NEW_STATUS"
        }

    :return: The new flat object in a JSON ``data`` dict.
    """
    try:
        flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
        if not flat:
            return bottle.HTTPError(404, "No flat with id {}.".format(flat_id))

        try:
            flat.status = getattr(
                flat_model.FlatStatus, json.load(bottle.request.body)["status"]
            )
        except (AttributeError, ValueError, KeyError):
            return bottle.HTTPError(400, "Invalid status provided.")

        return {
            "data": _serialize_flat(flat, config)
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def update_flat_notes_v1(flat_id, config, db):
    """
    API v1 route to update flat notes:

        POST /api/v1/flat/:flat_id/notes
        Data: {
            "notes": "NEW_NOTES"
        }

    :return: The new flat object in a JSON ``data`` dict.
    """
    try:
        flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
        if not flat:
            return bottle.HTTPError(404, "No flat with id {}.".format(flat_id))

        try:
            flat.notes = json.load(bottle.request.body)["notes"]
        except (ValueError, KeyError):
            return bottle.HTTPError(400, "Invalid notes provided.")

        return {
            "data": _serialize_flat(flat, config)
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def update_flat_notation_v1(flat_id, config, db):
    """
    API v1 route to update flat notation:

        POST /api/v1/flat/:flat_id/notation
        Data: {
            "notation": "NEW_NOTATION"
        }

    :return: The new flat object in a JSON ``data`` dict.
    """
    try:
        flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
        if not flat:
            return bottle.HTTPError(404, "No flat with id {}.".format(flat_id))

        try:
            flat.notation = json.load(bottle.request.body)["notation"]
            assert flat.notation >= 0 and flat.notation <= 5
        except (AssertionError, ValueError, KeyError):
            return bottle.HTTPError(400, "Invalid notation provided.")

        return {
            "data": _serialize_flat(flat, config)
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def update_flat_visit_date_v1(flat_id, config, db):
    """
    API v1 route to update flat date of visit:

        POST /api/v1/flat/:flat_id/visit_date
        Data: {
            "visit_date": "ISO8601 DATETIME"
        }

    :return: The new flat object in a JSON ``data`` dict.
    """
    try:
        flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
        if not flat:
            return bottle.HTTPError(404, "No flat with id {}.".format(flat_id))

        try:
            visit_date = json.load(bottle.request.body)["visit_date"]
            if visit_date:
                visit_date = arrow.get(visit_date).naive
            flat.visit_date = visit_date
        except (arrow.parser.ParserError, ValueError, KeyError):
            return bottle.HTTPError(400, "Invalid visit date provided.")

        return {
            "data": _serialize_flat(flat, config)
        }
    except Exception as e:
        return {
            "error": str(e)
        }


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
    except Exception as e:
        return {
            "error": str(e)
        }


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
            return bottle.HTTPError(400, "Invalid query provided.")

        flats_db_query = flat_model.Flat.search_query(db, query)
        flats = [
            _serialize_flat(flat, config)
            for flat in flats_db_query
        ]

        return {
            "data": flats
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def ics_feed_v1(config, db):
    """
    API v1 ICS feed of visits route:

        GET /api/v1/visits.ics

    :return: The ICS feed for the visits.
    """
    try:
        flats_with_visits = db.query(flat_model.Flat).filter(
            flat_model.Flat.visit_date.isnot(None)
        ).all()

        cal = vobject.iCalendar()
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

        return cal.serialize()
    except:
        return ''
