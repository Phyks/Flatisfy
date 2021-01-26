# coding: utf-8
"""
This module contains the definition of the web app API routes.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import itertools
import json
import re
import os

import bottle
import vobject

import flatisfy.data
from flatisfy.models import flat as flat_model
from flatisfy.models.postal_code import PostalCode

FILTER_RE = re.compile(r"filter\[([A-z0-9_]+)\]")


def JSONError(error_code, error_str):  # pylint: disable=invalid-name
    """
    Return an HTTP error with a JSON payload.

    :param error_code: HTTP error code to return.
    :param error_str: Error as a string.
    :returns: Set correct response parameters and returns JSON-serialized error
        content.
    """
    bottle.response.status = error_code
    bottle.response.content_type = "application/json"
    return json.dumps(dict(error=error_str, status_code=error_code))


def _JSONApiSpec(query, model, default_sorting=None):
    """
    Implementing JSON API spec for filtering, sorting and paginating results.

    :param query: A Bottle query dict.
    :param model: Database model used in this query.
    :param default_sorting: Optional field to sort on if no sort options are
        passed through parameters.
    :return: A tuple of filters, page number, page size (items per page) and
        sorting to apply.
    """
    # Handle filtering according to JSON API spec
    filters = {}
    for param in query:
        filter_match = FILTER_RE.match(param)
        if not filter_match:
            continue
        field = filter_match.group(1)
        value = query[filter_match.group(0)]
        filters[field] = value

    # Handle pagination according to JSON API spec
    page_number, page_size = 0, None
    try:
        if "page[size]" in query:
            page_size = int(query["page[size]"])
            assert page_size > 0
        if "page[number]" in query:
            page_number = int(query["page[number]"])
            assert page_number >= 0
    except (AssertionError, ValueError):
        raise ValueError("Invalid pagination provided.")

    # Handle sorting according to JSON API spec
    sorting = []
    if "sort" in query:
        for index in query["sort"].split(","):
            try:
                sort_field = getattr(model, index.lstrip("-"))
            except AttributeError:
                raise ValueError("Invalid sorting key provided: {}.".format(index))
            if index.startswith("-"):
                sort_field = sort_field.desc()
            sorting.append(sort_field)
    # Default sorting options
    if not sorting and default_sorting:
        try:
            sorting.append(getattr(model, default_sorting))
        except AttributeError:
            raise ValueError(
                "Invalid default sorting key provided: {}.".format(default_sorting)
            )

    return filters, page_number, page_size, sorting


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
            "gps": (postal_code_data.lat, postal_code_data.lng),
        }
    except (AssertionError, StopIteration):
        flat["flatisfy_postal_code"] = {}

    return flat


def index_v1():
    """
    API v1 index route.

    Example::

        GET /api/v1/
    """
    return {
        "opendata": "/api/v1/opendata",
        "flats": "/api/v1/flats",
        "flat": "/api/v1/flat/:id",
        "search": "/api/v1/search",
        "ics": "/api/v1/ics/visits.ics",
        "time_to_places": "/api/v1/time_to_places",
        "metadata": "/api/v1/metadata",
    }


def flats_v1(config, db):
    """
    API v1 flats route.

    Example::

        GET /api/v1/flats

    .. note::

        Filtering can be done through the ``filter`` GET param, according
        to JSON API spec (http://jsonapi.org/recommendations/#filtering).

    .. note::

        By default no pagination is done. Pagination can be forced using
        ``page[size]`` to specify a number of items per page and
        ``page[number]`` to specify which page to return. Pages are numbered
        starting from 0.

    .. note::

        Sorting can be handled through the ``sort`` GET param, according to
        JSON API spec (http://jsonapi.org/format/#fetching-sorting).

    :return: The available flats objects in a JSON ``data`` dict.
    """
    if bottle.request.method == "OPTIONS":
        # CORS
        return ""

    try:
        try:
            filters, page_number, page_size, sorting = _JSONApiSpec(
                bottle.request.query, flat_model.Flat, default_sorting="cost"
            )
        except ValueError as exc:
            return JSONError(400, str(exc))

        # Build flat list
        db_query = db.query(flat_model.Flat).filter_by(**filters).order_by(*sorting)
        flats = [
            _serialize_flat(flat, config)
            for flat in itertools.islice(
                db_query,
                page_number * page_size if page_size else None,
                page_number * page_size + page_size if page_size else None,
            )
        ]
        return {
            "data": flats,
            "page": page_number,
            "items_per_page": page_size if page_size else len(flats),
        }
    except Exception as exc:  # pylint: disable= broad-except
        return JSONError(500, str(exc))


def flat_v1(flat_id, config, db):
    """
    API v1 flat route.

    Example::

        GET /api/v1/flats/:flat_id

    :return: The flat object in a JSON ``data`` dict.
    """
    if bottle.request.method == "OPTIONS":
        # CORS
        return {}

    try:
        flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()

        if not flat:
            return JSONError(404, "No flat with id {}.".format(flat_id))

        return {"data": _serialize_flat(flat, config)}
    except Exception as exc:  # pylint: disable= broad-except
        return JSONError(500, str(exc))


def update_flat_v1(flat_id, config, db):
    """
    API v1 route to update flat status.

    Example::

        PATCH /api/v1/flat/:flat_id
        Data: {
            "status": "NEW_STATUS",
            "visit_date": "ISO8601 DATETIME"
        }

    .. note::

        The keys in the data sent are same keys as in ``Flat`` model. You
        can provide any subset of them to update part of the flat infos.

    :return: The new flat object in a JSON ``data`` dict.
    """
    if bottle.request.method == "OPTIONS":
        # CORS
        return {}

    try:
        flat = db.query(flat_model.Flat).filter_by(id=flat_id).first()
        if not flat:
            return JSONError(404, "No flat with id {}.".format(flat_id))

        try:
            json_body = json.load(bottle.request.body)
            for key, value in json_body.items():
                setattr(flat, key, value)
        except ValueError as exc:
            return JSONError(400, "Invalid payload provided: {}.".format(str(exc)))

        return {"data": _serialize_flat(flat, config)}
    except Exception as exc:  # pylint: disable= broad-except
        return JSONError(500, str(exc))


def time_to_places_v1(config):
    """
    API v1 route to fetch the details of the places to compute time to.

    Example::

        GET /api/v1/time_to_places

    :return: The JSON dump of the places to compute time to (dict of places
        names mapped to GPS coordinates).
    """
    if bottle.request.method == "OPTIONS":
        # CORS
        return {}

    try:
        places = {}
        for constraint_name, constraint in config["constraints"].items():
            places[constraint_name] = {
                k: v["gps"] for k, v in constraint["time_to"].items()
            }
        return {"data": places}
    except Exception as exc:  # pylint: disable= broad-except
        return JSONError(500, str(exc))


def search_v1(db, config):
    """
    API v1 route to perform a fulltext search on flats.

    Example::

        POST /api/v1/search
        Data: {
            "query": "SOME_QUERY"
        }

    .. note::

        Filtering can be done through the ``filter`` GET param, according
        to JSON API spec (http://jsonapi.org/recommendations/#filtering).

    .. note::

        By default no pagination is done. Pagination can be forced using
        ``page[size]`` to specify a number of items per page and
        ``page[number]`` to specify which page to return. Pages are numbered
        starting from 0.

    .. note::

        Sorting can be handled through the ``sort`` GET param, according to
        JSON API spec (http://jsonapi.org/format/#fetching-sorting).

    :return: The matching flat objects in a JSON ``data`` dict.
    """
    if bottle.request.method == "OPTIONS":
        # CORS
        return {}

    try:
        try:
            query = json.load(bottle.request.body)["query"]
        except (ValueError, KeyError):
            return JSONError(400, "Invalid query provided.")

        try:
            filters, page_number, page_size, sorting = _JSONApiSpec(
                bottle.request.query, flat_model.Flat, default_sorting="cost"
            )
        except ValueError as exc:
            return JSONError(400, str(exc))

        flats_db_query = (
            flat_model.Flat.search_query(db, query)
            .filter_by(**filters)
            .order_by(*sorting)
        )
        flats = [
            _serialize_flat(flat, config)
            for flat in itertools.islice(
                flats_db_query,
                page_number * page_size if page_size else None,
                page_number * page_size + page_size if page_size else None,
            )
        ]

        return {
            "data": flats,
            "page": page_number,
            "items_per_page": page_size if page_size else len(flats),
        }
    except Exception as exc:  # pylint: disable= broad-except
        return JSONError(500, str(exc))


def ics_feed_v1(config, db):
    """
    API v1 ICS feed of visits route.

    Example::

        GET /api/v1/ics/visits.ics

    :return: The ICS feed for the visits.
    """
    if bottle.request.method == "OPTIONS":
        # CORS
        return {}

    cal = vobject.iCalendar()
    try:
        flats_with_visits = db.query(flat_model.Flat).filter(
            flat_model.Flat.visit_date.isnot(None)
        )

        for flat in flats_with_visits:
            vevent = cal.add("vevent")
            vevent.add("dtstart").value = flat.visit_date
            vevent.add("dtend").value = flat.visit_date + datetime.timedelta(hours=1)
            vevent.add("summary").value = "Visit - {}".format(flat.title)

            description = "{} (area: {}, cost: {} {})\n{}#/flat/{}\n".format(
                flat.title,
                flat.area,
                flat.cost,
                flat.currency,
                config["website_url"],
                flat.id,
            )
            description += "\n{}\n".format(flat.text)
            if flat.notes:
                description += "\n{}\n".format(flat.notes)

            vevent.add("description").value = description
    except Exception:  # pylint: disable= broad-except
        pass

    return cal.serialize()


def opendata_index_v1():
    """
    API v1 data index route.

    Example::

        GET /api/v1/opendata
    """
    if bottle.request.method == "OPTIONS":
        # CORS
        return {}

    return {"postal_codes": "/api/v1/opendata/postal_codes"}


def opendata_postal_codes_v1(db):
    """
    API v1 data postal codes route.

    Example::

        GET /api/v1/opendata/postal_codes

    .. note::

        Filtering can be done through the ``filter`` GET param, according
        to JSON API spec (http://jsonapi.org/recommendations/#filtering).

    .. note::

        By default no pagination is done. Pagination can be forced using
        ``page[size]`` to specify a number of items per page and
        ``page[number]`` to specify which page to return. Pages are numbered
        starting from 0.

    .. note::

        Sorting can be handled through the ``sort`` GET param, according to
        JSON API spec (http://jsonapi.org/format/#fetching-sorting).


    :return: The postal codes data from opendata.
    """
    if bottle.request.method == "OPTIONS":
        # CORS
        return {}

    try:
        try:
            filters, page_number, page_size, sorting = _JSONApiSpec(
                bottle.request.query, PostalCode, default_sorting="postal_code"
            )
        except ValueError as exc:
            return JSONError(400, str(exc))

        db_query = db.query(PostalCode).filter_by(**filters).order_by(*sorting)
        postal_codes = [
            x.json_api_repr()
            for x in itertools.islice(
                db_query,
                page_number * page_size if page_size else None,
                page_number * page_size + page_size if page_size else None,
            )
        ]
        return {
            "data": postal_codes,
            "page": page_number,
            "items_per_page": page_size if page_size else len(postal_codes),
        }
    except Exception as exc:  # pylint: disable= broad-except
        return JSONError(500, str(exc))


def metadata_v1(config):
    """
    API v1 metadata of the application.

    Example::

        GET /api/v1/metadata

    :return: The application metadata.
    """
    if bottle.request.method == "OPTIONS":
        # CORS
        return {}

    try:
        last_update = None
        try:
            ts_file = os.path.join(config["data_directory"], "timestamp")
            last_update = os.path.getmtime(ts_file)
        except OSError:
            pass

        return {"data": {"last_update": last_update}}
    except Exception as exc:  # pylint: disable= broad-except
        return JSONError(500, str(exc))
