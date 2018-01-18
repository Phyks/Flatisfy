# coding : utf-8
"""
Preprocessing functions to convert input opendata files into SQLAlchemy objects
ready to be stored in the database.
"""
import csv
import io
import json
import logging
import os
import sys

if sys.version_info >= (3,0):
    import csv
else:
    from backports import csv

from flatisfy.models.postal_code import PostalCode
from flatisfy.models.public_transport import PublicTransport


LOGGER = logging.getLogger(__name__)
MODULE_DIR = os.path.dirname(os.path.realpath(__file__))

TRANSPORT_DATA_FILES = {
    "FR-IDF": "stops_fr-idf.txt",
    "FR-NW": "stops_fr-nw.txt",
    "FR-NE": "stops_fr-ne.txt",
    "FR-SW": "stops_fr-sw.txt",
    "FR-SE": "stops_fr-se.txt"
}


def french_postal_codes_to_quarter(postal_code):
    """
    Convert a French postal code to the main quarter in France this postal
    code belongs to.

    :param postal_code: The postal code to convert.
    :returns: The quarter of France or ``None``.
    """
    departement = postal_code[:2]

    # Mapping between areas (main subdivisions in French, ISO 3166-2) and
    # French departements
    # Taken from Wikipedia data.
    department_to_subdivision = {
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
    subdivision_to_quarters = {
        'FR-IDF': ['FR-IDF'],
        'FR-NW': ['FR-BRE', 'FR-CVL', 'FR-NOR', 'FR-PDL'],
        'FR-NE': ['FR-BFC', 'FR-GES', 'FR-HDF'],
        'FR-SE': ['FR-ARA', 'FR-COR', 'FR-PAC', 'FR-OCC'],
        'FR-SW': ['FR-NAQ']
    }

    subdivision = next(
        (
            i
            for i, departments in department_to_subdivision.items()
            if departement in departments
        ),
        None
    )
    return next(
        (
            i
            for i, subdivisions in subdivision_to_quarters.items()
            if subdivision in subdivisions
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
        with io.open(
            os.path.join(MODULE_DIR, data_file), "r", encoding='utf-8'
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
            area = french_postal_codes_to_quarter(fields["code_postal"])
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


def _preprocess_public_transport():
    """
    Build SQLAlchemy objects from the Navitia public transport data.

    :return: A list of ``PublicTransport`` objects to be inserted in database.
    """
    public_transport_data = []
    # Load opendata file
    for area, data_file in TRANSPORT_DATA_FILES.items():
        LOGGER.info("Building from public transport data %s.", data_file)
        try:
            with io.open(os.path.join(MODULE_DIR, data_file), "r",
                         encoding='utf-8') as fh:
                filereader = csv.reader(fh)
                next(filereader, None)  # Skip first row (headers)
                for row in filereader:
                    public_transport_data.append(PublicTransport(
                        name=row[2],
                        area=area,
                        lat=row[3],
                        lng=row[4]
                    ))
        except (IOError, IndexError):
            LOGGER.error("Invalid raw opendata file: %s.", data_file)
            return []

    return public_transport_data


# List of all the available preprocessing functions. Order can be important.
PREPROCESSING_FUNCTIONS = [
    _preprocess_laposte,
    _preprocess_public_transport
]
