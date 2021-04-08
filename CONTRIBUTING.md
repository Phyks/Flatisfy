## TL;DR

We have a [code of conduct](CodeOfConduct.md), please make sure to review it
prior to contributing.

* Branch off `master`.
* One feature per commit.
* In case of changes request, amend your commit.

You can either open issues / merge requests on [my
Gitlab](https://git.phyks.me/Phyks/flatisfy/) (preferred) or on the [Github
mirror](https://github.com/phyks/flatisfy).


## Useful infos

* There is a `hooks/pre-commit` file which can be used as a `pre-commit` git
  hook to check coding style.
* Python coding style is PEP8. JS coding style is enforced by `eslint`.
* Some useful `npm` scripts are provided (`build:{dev,prod}` /
  `watch:{dev,prod}` / `lint`)


## Translating the webapp

If you want to translate the webapp, just create a new folder in
`flatisfy/web/js_src/i18n` with the short name of your locale (typically, `en`
is for english). Copy the `flatisfy/web/js_src/i18n/en/index.js` file to this
new folder and translate the `messages` strings.

Then, edit `flatisfy/web/js_src/i18n/index.js` file to include your new
locale.


## How to contribute

* If you're thinking about a new feature, see if there's already an issue open
  about it, or please open one otherwise. This will ensure that everybody is on
  track for the feature and willing to see it in Flatisfy.
* One commit per feature.
* Branch off the `master ` branch.
* Check the linting of your code before doing a PR.
* Ideally, your merge-request should be mergeable without any merge commit, that
  is, it should be a fast-forward merge. For this to happen, your code needs to
  be always rebased onto `master`. Again, this is something nice to have that
  I expect from recurring contributors, but not a big deal if you don't do it
  otherwise.
* I'll look at it and might ask for a few changes. In this case, please create
  new commits. When the final result looks good, I may ask you to squash the
  WIP commits into a single one, to maintain the invariant of "one feature, one
  commit".

Thanks!


## Adding support for a new Woob backend

To enable a new Woob `CapHousing` backend in Flatisfy, you should add it to
the list of available backends in
[flatisfy/fetch.py#L69-70](https://git.phyks.me/Phyks/flatisfy/blob/master/flatisfy/fetch.py#L69-70)
and update the list of `BACKEND_PRECEDENCES` for deduplication in
[flatisfy/filters/duplicates.py#L24-31](https://git.phyks.me/Phyks/flatisfy/blob/master/flatisfy/filters/duplicates.py#L24-31).
Thats' all!


## Adding new data files

If you want to add new data files, especially for public transportation stops
(to cover more cities), please follow these steps:

1. Download and put the **original** file in `flatisfy/data_files`. Please,
   use the original data file to ease tracking licenses and be able to still
   have a working pipeline, by letting the user download it and place it in
   the right place, in case of license conflict.
2. Mention the added data file and its license in `README.md`, in the
   dedicated section.
3. Write a preprocessing function in `flatisfy/data_files/__init__.py`. You
   can have a look at the existing functions for a model.


## Adding new migrations

If you want to change the database schema, you should create a matching
migration. Here is the way to do it correctly:

1. First, edit the `flatisfy/models` files to create / remove the required
   fields. If you create a new database from scratch, these are the files
   which will be used.
2. Then, run `alembic revision -m "Some description"` in the root of the git
   repo to create a new migration.
3. Finally, edit the newly created migration file under the `migrations/`
   folder to add the required code to alter the database (both upgrade and
   downgrade).


Thanks!
