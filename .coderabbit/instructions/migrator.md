---
id: migrator
name: Legacy data migrator
paths:
  - "migrator/**"
  - "scripts/deploy_checklist.py"
---

`migrator/` is the legacy-Zenodo → InvenioRDM data migrator (`zenodo-rdm-migrator`,
built on `invenio-rdm-migrator`). It is a separate setuptools package (its own
`setup.cfg`/`setup.py`, MIT-metadata but SPDX GPL-3.0 headers) and is **not** a
uv workspace member. It is driven by `python -m zenodo_rdm_migrator
/path/to/streams.yaml`.

The pipeline is: `scripts/*.sql` dump the legacy database (users, communities,
records, drafts, requests, files, deleted records, OAuth2 clients/tokens,
GitHub, webhooks), `transform/` maps legacy rows into RDM entries
(`transform/entries/` plus per-stream transformers), and `actions/` load them
into the RDM database. Streams are configured in `streams.yaml`.

Review for:

- **Data fidelity.** Transformed values must round-trip the legacy meaning.
  Flag dropped fields, lossy date/identifier formatting, or a mapping that
  changes the value semantics (licenses, funders, resource types, access
  rights).
- **Matching correctness.** Streams that match existing records (communities
  cache, parents/versioning) must not mis-associate rows. False positives
  corrupt relationships; false negatives create duplicates. Check identifier
  normalisation (DOIs, arXiv, report numbers, OAuth client ids).
- **Idempotency and resumability.** Streams support `existing_data: true` to
  skip re-extract/transform. A new stream or action must be re-runnable without
  duplicating rows, and must not assume a fresh database (fixtures and the
  `id=1` user clash are a known trap — see `migrator/README.md`).
- **Versioning.** The versions table generator runs once against the shared
  parents cache after all record changes are applied. Flag changes that make
  version grouping order-dependent.
- **Failure isolation.** One bad legacy row must be logged with its source id
  and skipped, not abort the whole stream or leave partial state.
- **No clobbering.** Loading must not overwrite data another stream already
  wrote. Watch for cross-stream ordering assumptions.
- Migrator code is formatted with black + isort + pydocstyle via its own pytest
  (`migrator/setup.cfg`). Don't suggest ruff/flake8/pylint rules.
