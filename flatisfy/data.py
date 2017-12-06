# coding : utf-8
"""
This module contains all the code related to building necessary data files from
the source opendata files.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging

import flatisfy.exceptions

from flatisfy import database
from flatisfy import data_files
from flatisfy.models.postal_code import PostalCode
from flatisfy.models.public_transport import PublicTransport
from flatisfy.tools import hash_dict

LOGGER = logging.getLogger(__name__)

# Try to load lru_cache
try:
    from functools import lru_cache
except ImportError:
    try:
        from functools32 import lru_cache
    except ImportError:
        def lru_cache(maxsize=None):  # pylint: disable=unused-argument
            """
            Identity implementation of ``lru_cache`` for fallback.
            """
            return lambda func: func
        LOGGER.warning(
            "`functools.lru_cache` is not available on your system. Consider "
            "installing `functools32` Python module if using Python2 for "
            "better performances."
        )


def preprocess_data(config, force=False):
    """
    Ensures that all the necessary data have been inserted in db from the raw
    opendata files.

    :params config: A config dictionary.
    :params force: Whether to force rebuild or not.
    :return bool: Whether data have been built or not.
    """
    # Check if a build is required
    get_session = database.init_db(config["database"], config["search_index"])
    with get_session() as session:
        is_built = (
            session.query(PublicTransport).count() > 0 and
            session.query(PostalCode).count() > 0
        )
        if is_built and not force:
            # No need to rebuild the database, skip
            return False
        # Otherwise, purge all existing data
        session.query(PublicTransport).delete()
        session.query(PostalCode).delete()

    # Build all opendata files
    LOGGER.info("Rebuilding data...")
    for preprocess in data_files.PREPROCESSING_FUNCTIONS:
        data_objects = preprocess()
        if not data_objects:
            raise flatisfy.exceptions.DataBuildError(
                "Error with %s." % preprocess.__name__
            )
        with get_session() as session:
            session.add_all(data_objects)
    LOGGER.info("Done building data!")
    return True


@hash_dict
@lru_cache(maxsize=5)
def load_data(model, constraint, config):
    """
    Load data of the specified model from the database. Only load data for the
    specific areas of the postal codes in config.

    :param model: SQLAlchemy model to load.
    :param constraint: A constraint from configuration to limit the spatial
    extension of the loaded data.
    :param config: A config dictionary.
    :returns: A list of loaded SQLAlchemy objects from the db
    """
    get_session = database.init_db(config["database"], config["search_index"])
    results = []
    with get_session() as session:
        areas = []
        # Get areas to fetch from, using postal codes
        for postal_code in constraint["postal_codes"]:
            areas.append(data_files.french_postal_codes_to_quarter(postal_code))
        # Load data for each area
        areas = list(set(areas))
        for area in areas:
            results.extend(
                session.query(model)
                .filter(model.area == area).all()
            )
        # Expunge loaded data from the session to be able to use them
        # afterwards
        session.expunge_all()
    return results
