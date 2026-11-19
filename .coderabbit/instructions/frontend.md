---
id: frontend-js
name: React/JS assets and overrides
paths:
  - "assets/**"
  - "site/zenodo_rdm/assets/**"
  - "site/zenodo_rdm/webpack.py"
  - "package.json"
  - "site/package.json"
  - "pnpm-workspace.yaml"
---

- The UI is React 18 + Semantic UI React, bundled by Invenio's asset pipeline
  using **rspack** (configured via `WEBPACKEXT_PROJECT =
  "invenio_assets.webpack:rspack_project"` in `invenio.cfg`), not Webpack. Root
  `assets/` customises upstream components through `react-overridable`.
  Overrides are registered in
  `assets/js/invenio_app_rdm/overridableRegistry/mapping.js` under the exact
  upstream overridable id. A new override that isn't registered there, or a
  misspelt id, silently does nothing. Flag both.
- An override replaces the upstream component wholesale. Check that it keeps
  the props contract and behaviour of the upstream component it replaces
  (accessibility, loading/error states, i18n). Point out logic copied from
  upstream that has diverged.
- New JS entry points and LESS for `zenodo_rdm` features must be declared in
  `site/zenodo_rdm/webpack.py`. New npm dependencies go there and must be
  compatible with the versions `invenio-app-rdm` pins.
- Use `@translations/invenio_app_rdm/i18next` (or the module's i18next) for
  user-visible strings.
- API calls go through the existing API clients (`http` from
  `react-invenio-forms`/`@js/invenio_rdm_records`). They need error handling and
  should cancel in-flight requests on unmount.
- Never render HTML from record metadata with `dangerouslySetInnerHTML`
  without sanitising it.
- Linting is `@inveniosoftware/eslint-config-invenio` with the
  `react18` + `prettier` configs (run through `./run-js-linter.sh`). Don't
  repeat lint or prettier findings.
