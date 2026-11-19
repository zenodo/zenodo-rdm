---
id: zenodo-rdm-overview
name: Zenodo-RDM overview and general rules
---

Zenodo-RDM is the Zenodo **instance** built on InvenioRDM. It is not a library.
The repository is a uv workspace: the root `pyproject.toml` pulls in
`invenio-app-rdm` and the `zenodo-legacy` / `zenodo-rdm` packages, and the
workspace members are `site/` (ships `zenodo_rdm`) and `legacy/` (ships
`zenodo_legacy`). `migrator/` is a separate, self-contained package
(`zenodo-rdm-migrator`, setuptools/`setup.cfg`) that is **not** part of the uv
workspace and migrates legacy Zenodo data into RDM.

Where code belongs:

- `site/zenodo_rdm/` holds instance Python code: permission policies and
  generators, the legacy REST compatibility layer, OpenAIRE integration,
  metrics, moderation, exporter, curation, VCS/GitHub release ingestion,
  subcommunities, support forms, the theme, serializers, resources, custom
  fields, checks, partners (Dryad/LoRy/Plazi), previewer and facets.
- `legacy/zenodo_legacy/` holds the `zenodo-legacy` package: legacy funder and
  license vocabulary data used by the compatibility layer.
- `migrator/zenodo_rdm_migrator/` holds the legacy→RDM data migration streams.
- `invenio.cfg` holds instance configuration. `site/zenodo_rdm/config.py` and
  the per-extension `config.py` files hold config defaults for `zenodo_rdm`
  extensions.
- `app_data/` holds fixtures and controlled vocabularies.
- `assets/` and `templates/` at the root hold UI overrides of upstream
  packages. `site/zenodo_rdm/assets/` and `site/zenodo_rdm/templates/` hold UI
  that belongs to `zenodo_rdm` features.
- Entry points (blueprints, apps, tasks, request types, access actions, idutils
  schemes, index templates, checks, jobs, db models, oauth2 scopes, moderation
  actions) are registered in `site/pyproject.toml`. A new module that isn't
  registered there is dead code. Flag it.

When reviewing:

- If a change works around generic InvenioRDM behaviour (records, drafts,
  communities, requests, vocabularies, files), ask whether it belongs upstream
  in an `invenio-*` package. Monkeypatching upstream classes is a red flag.
  Prefer config, components, generators and overridable hooks.
- Every source file keeps an SPDX license header: a
  `SPDX-FileCopyrightText: YYYY CERN` line (additional copyright holders are
  listed as extra lines) and `SPDX-License-Identifier: GPL-3.0-or-later`.
  Edited files extend the year range. `__init__.py` files carry the header too.
- Python formatting is `black` (88-character lines) and import ordering is
  `isort` with `profile = black`. `isort` and `pydocstyle` run through pytest
  (`--isort --pydocstyle`), so CI fails on violations; `black` is run by the
  migrator's pytest. `pydocstyle` ignores D401 and D403, so public modules,
  classes and functions still need a docstring. Do not suggest ruff, flake8 or
  pylint rules, or style changes that conflict with black or isort.
- User-facing strings go through `invenio_i18n` (`_` / `lazy_gettext`) in
  Python and `i18next` in JS. Flag hard-coded English in the UI.
- Do not comment on formatting that `black`/`isort`/`eslint`/`prettier` already
  enforce.
