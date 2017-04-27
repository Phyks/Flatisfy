## TL;DR

* Branch off `master`.
* One feature per commit.
* In case of changes request, amend your commit.


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