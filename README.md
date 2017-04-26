Flatisfy
========

Flatisfy is your new companion to ease your search of a new housing :)


**Note**: This software is under heavy development at the moment, and the
database schema could change at any time. Do not consider it as being
production ready. However, I am currently using it for my own housing search
and it is working fine :)


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
   Edit it according to your needs (see doc).
4. Build the required data files:
   `python -m flatisfy build-data --config config.json`.
5. Use it to `fetch` (and output a filtered JSON list of flats) or `import`
   (into an SQLite database, for the web visualization) a list of flats
   matching your criteria.
6. Install JS libraries and build the webapp:
   `npm install && npm run build:dev` (use `build:prod` in production).
7. Use `python -m flatisfy serve --config config.json` to serve the web app.


## Documentation

See the [dedicated folder](doc/).


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


## Contributing

See the `CONTRIBUTING.md` file for more infos.


## Thanks

* [Weboob](http://weboob.org/)
* The OpenData providers listed above!
* Navitia for their really cool public transportation API.
* A lots of Python modules, required for this script (see `requirements.txt`).
* [Kresus](https://framagit.org/bnjbvr/kresus) which gave me part of the
  original idea (at least proved me such software based on scraping can
  achieve a high quality level :)
* Current favicon is from [Wikipedia](https://commons.wikimedia.org/wiki/File:Home_Icon.svg)
