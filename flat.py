# coding: utf-8
#!/usr/bin/env python3
import json
import os
import subprocess
import sys

from fuzzywuzzy import process as fuzzyprocess

import config


def pretty_json(json_str):
    return json.dumps(json_str, indent=4, separators=(',', ': '),
                      sort_keys=True)


def preprocess_data():
    if not os.path.isdir("build"):
        os.mkdir("build")

    if not os.path.isfile("build/ratp.json"):
        ratp_data = []
        with open("data/ratp.json", "r") as fh:
            ratp_data = json.load(fh)
        ratp_data = sorted(
            list(set(
                x["fields"]["stop_name"].lower() for x in ratp_data
            ))
        )
        with open("build/ratp.json", "w") as fh:
            fh.write(pretty_json(ratp_data))


def fetch_flats_list():
    flats_list = []
    for query in config.QUERIES:
        flatboob_output = subprocess.check_output(
            ["flatboob", "-n", "0", "-f", "json", "load", query]
        )
        flats_list.extend(json.loads(flatboob_output))
    return flats_list


def remove_duplicates(flats_list):
    unique_flats_list = []
    ids = []
    for flat in flats_list:
        if flat["id"] in ids:
            continue
        ids.append(id)
        unique_flats_list.append(flat)
    return unique_flats_list


def sort_by(flats_list, key="cost"):
    return sorted(flats_list, key=lambda x: x["cost"])


def refine_params(flats_list):
    def filter_conditions(x):
        is_ok = True
        if "cost" in x:
            cost = x["cost"]
            is_ok = (
                is_ok and
                (cost < config.PARAMS["max_cost"] and
                 cost > config.PARAMS["min_cost"])
            )
        if "area" in x:
            area = x["area"]
            is_ok = (
                is_ok and
                (area < config.PARAMS["max_area"] and
                 area > config.PARAMS["min_area"])
            )
        return is_ok

    return filter(filter_conditions, flats_list)


def match_ratp(flats_list):
    ratp_stations = []
    with open("build/ratp.json", "r") as fh:
        ratp_stations = json.load(fh)

    for flat in flats_list:
        if "station" in flat and flat["station"]:
            # There is some station fetched by flatboob, try to match it
            flat["ratp_station"] = fuzzyprocess.extractOne(
                flat["station"], ratp_stations
            )
            # TODO: Cross-check station location to choose the best fit

    return flats_list


def main(dumpfile=None):
    if dumpfile is None:
        flats_list = fetch_flats_list()
    else:
        with open(dumpfile, "r") as fh:
            flats_list = json.load(fh)

    # First pass
    flats_list = remove_duplicates(flats_list)
    flats_list = sort_by(flats_list, "cost")
    flats_list = refine_params(flats_list)

    # TODO: flats_list = match_ratp(flats_list)

    # TODO: Second pass, loading additional infos for each entry

    return flats_list


if __name__ == "__main__":
    if len(sys.argv) > 1:
        dumpfile = sys.argv[1]
    else:
        dumpfile = None

    try:
        preprocess_data()
        flats_list = main(dumpfile)
        print(
            pretty_json(flats_list)
        )
    except KeyboardInterrupt:
        pass
