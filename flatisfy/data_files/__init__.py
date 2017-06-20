# coding : utf-8
"""
Preprocessing functions to convert input opendata files into SQLAlchemy objects
ready to be stored in the database.
"""
import json
import logging
import os

from flatisfy.models.postal_code import PostalCode
from flatisfy.models.public_transport import PublicTransport


LOGGER = logging.getLogger(__name__)
MODULE_DIR = os.path.dirname(os.path.realpath(__file__))


def french_postal_codes_to_iso_3166(postal_code):
    """
    Convert a French postal code to the main subdivision in French this postal
    code belongs to (ISO 3166-2 code).

    :param postal_code: The postal code to convert.
    :returns: The ISO 3166-2 code of the subdivision or ``None``.
    """
    # Mapping between areas (main subdivisions in French, ISO 3166-2) and
    # French departements
    # Taken from Wikipedia data.
    area_to_departement = {
        "FR-ARA": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69",
                   "73", "74"],
        "FR-BFC": ["21", "25", "39", "58", "70", "71", "89", "90"],
        "FR-BRE": ["22", "29", "35", "44", "56"],
        "FR-CVL": ["18", "28", "36", "37", "41", "45"],
        "FR-COR": ["20"],
        "FR-GES": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
        "FR-HDF": ["02", "59", "60", "62", "80"],
        "FR-IDF": ["75", "77", "78", "91", "92", "93", "94", "95"],
        "FR-NOR": ["14", "27", "50", "61", "76"],
        "FR-NAQ": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79",
                   "86", "87"],
        "FR-OCC": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65",
                   "66", "81", "82"],
        "FR-PDL": ["44", "49", "53", "72", "85"],
        "FR-PAC": ["04", "05", "06", "13", "83", "84"]
    }

    departement = postal_code[:2]
    return next(
        (
            i
            for i in area_to_departement
            if departement in area_to_departement[i]
        ),
        None
    )



def _preprocess_laposte():
    """
    Build SQLAlchemy objects from the postal codes data.

    :return: A list of ``PostalCode`` objects to be inserted in database.
    """
    data_file = "laposte.json"
    LOGGER.info("Building from %s data.", data_file)

    raw_laposte_data = []
    # Load opendata file
    try:
        with open(
            os.path.join(MODULE_DIR, data_file), "r"
        ) as fh:
            raw_laposte_data = json.load(fh)
    except (IOError, ValueError):
        LOGGER.error("Invalid raw LaPoste opendata file.")
        return []

    # Build postal codes to other infos file
    postal_codes_data = []
    for item in raw_laposte_data:
        fields = item["fields"]
        try:
            area = french_postal_codes_to_iso_3166(fields["code_postal"])
            if area is None:
                LOGGER.info(
                    "No matching area found for postal code %s, skipping it.",
                    fields["code_postal"]
                )
                continue

            postal_codes_data.append(PostalCode(
                area=area,
                postal_code=fields["code_postal"],
                name=fields["nom_de_la_commune"].title(),
                lat=fields["coordonnees_gps"][0],
                lng=fields["coordonnees_gps"][1]
            ))
        except KeyError:
            LOGGER.info("Missing data for postal code %s, skipping it.",
                        fields["code_postal"])

    return postal_codes_data


def _preprocess_ratp():
    """
    Build SQLAlchemy objects from the RATP data (public transport in Paris,
    France).

    :return: A list of ``PublicTransport`` objects to be inserted in database.
    """
    data_file = "ratp.json"
    LOGGER.info("Building from %s data.", data_file)

    ratp_data_raw = []
    # Load opendata file
    try:
        with open(os.path.join(MODULE_DIR, data_file), "r") as fh:
            ratp_data_raw = json.load(fh)
    except (IOError, ValueError):
        LOGGER.error("Invalid raw RATP opendata file.")
        return []

    # Process it
    ratp_data = []
    for item in ratp_data_raw:
        fields = item["fields"]
        ratp_data.append(PublicTransport(
            name=fields["stop_name"],
            area="FR-IDF",
            lat=fields["coord"][0],
            lng=fields["coord"][1]
        ))
    return ratp_data


def _preprocess_tcl():
    """
    Build SQLAlchemy objects from the Tcl data (public transport in Lyon,
    France).

    :return: A list of ``PublicTransport`` objects to be inserted in database.
    """
    data_file = "tcl.json"
    LOGGER.info("Building from %s data.", data_file)

    tcl_data_raw = []
    # Load opendata file
    try:
        with open(os.path.join(MODULE_DIR, data_file), "r") as fh:
            tcl_data_raw = json.load(fh)
    except (IOError, ValueError):
        LOGGER.error("Invalid raw Tcl opendata file.")
        return []

    # Process it
    tcl_data = []
    for item in tcl_data_raw["features"]:
        tcl_data.append(PublicTransport(
            name=item["properties"]["nom"],
            area="FR-ARA",
            lat=item["geometry"]["coordinates"][1],
            lng=item["geometry"]["coordinates"][0]
        ))
    return tcl_data


# List of all the available preprocessing functions. Order can be important.
PREPROCESSING_FUNCTIONS = [
    _preprocess_laposte,
    _preprocess_ratp,
    _preprocess_tcl
]
