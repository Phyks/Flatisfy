Flatisfy
========

Flatisfy is your new companion to ease your search of a new housing :)


It uses [Weboob](http://weboob.org/) to get all the housing posts on most of
the websites offering housings posts, and then offers a bunch of pipelines to
filter and deduplicate the fetched housings.


It can be used as a command-line utility, but also exposes a web API and
visualisation, to browse through the results.


_Note_: It is targeted at French users (due to the currently supported
websites), and in particular at people living close to Paris, as I developped
it for my personal use, and am currently living in Paris :) Any feedback and
merge requests to better support other countries / cities are more than
welcome!

_Note_: In this repository and across the code, I am using the name "flat". I
use it as a placeholder for "housing" and consider both are interchangeable.
This code is not restricted to handling flats only!


## Getting started

1. Clone the repository.
2. Install required Python modules: `pip install -r requirements.txt`.
3. Init a configuration file: `python -m flatisfy init-config > config.json`.
   Edit it according to your needs (see below).
4. Build the required data files:
   `python -m flatisfy build-data --config config.json`.
5. Use it to `fetch` (and output a filtered JSON list of flats) or `import`
   (into an SQLite database, for the web visualization) a list of flats
   matching your criteria.
6. Use `python -m flatisfy serve --config config.json` to serve the web app.


## Configuration

List of configuration options:

* `data_directory` is the directory in which you want data files to be stored.
  `null` is the default value and means default `XDG` location (typically
  `~/.local/share/flatisfy/`)
* `max_entries` is the maximum number of entries to fetch **per Weboob
  backend** (that is per housing website).
* `passes` is the number of passes to run on the data. First pass is a basic
  filtering and using only the informations from the housings list page.
  Second pass loads any possible information about the filtered flats and does
  better filtering.
* `queries` is a list of queries defined in `flatboob` that should be fetched.
* `database` is an SQLAlchemy URI to a database file. Defaults to `null` which
  means that it will store the database in the default location, in
  `data_directory`.
* `navitia_api_key` is an API token for [Navitia](https://www.navitia.io/)
  which is required to compute travel times.

### Constraints

You can specify constraints, under the `constraints` key. The available
constraints are:

* `area` (in m²), `bedrooms`, `cost` (in currency unit), `rooms`: this is a
  tuple of `(min, max)` values, defining an interval in which the value should
  lie. A `null` value means that any value is within this bound.
* `postal_codes` is a list of allowed postal codes. You should include any
  postal code you want, and especially the postal codes close to the precise
  location you want. You MUST provide some postal codes.
* `time_to` is a dictionary of places to compute travel time to them.
  Typically,
  ```
  "time_to": {
    "foobar": {
        "gps": [LAT, LNG],
        "time": [min, max]
    }
  }
  ```
  means that the housings must be between the `min` and `max` bounds (possibly
  `null`) from the place identified by the GPS coordinates `LAT` and `LNG`
  (latitude and longitude), and we call this place `foobar` in human-readable
  form. Beware that `time` constraints are in **seconds**.


## OpenData

I am using the following datasets, available under `flatisfy/data_files`,
which covers Paris. If you want to run the script using some other location,
you might have to change these files by matching datasets.

* [LaPoste Hexasmal](https://datanova.legroupe.laposte.fr/explore/dataset/laposte_hexasmal/?disjunctive.code_commune_insee&disjunctive.nom_de_la_commune&disjunctive.code_postal&disjunctive.libell_d_acheminement&disjunctive.ligne_5) for the list of cities and postal codes in France.
* [RATP stations](https://data.ratp.fr/explore/dataset/positions-geographiques-des-stations-du-reseau-ratp/table/?disjunctive.stop_name&disjunctive.code_postal&disjunctive.departement) for the list of subway stations with their positions in Paris and nearby areas.

Both datasets are licensed under the Open Data Commons Open Database License
(ODbL): https://opendatacommons.org/licenses/odbl/.


## License

The content of this repository is licensed under an MIT license, unless
explicitly mentionned otherwise.


## Thanks

* [Weboob](http://weboob.org/)
* The OpenData providers listed above!
* Navitia for their really cool public transportation API.
* A lots of Python modules, required for this script (see `requirements.txt`).
* [Kresus](https://framagit.org/bnjbvr/kresus) which gave me part of the
  original idea (at least proved me such software based on scraping can
  achieve a high quality level :)
