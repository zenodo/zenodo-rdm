---
id: database-models
name: Database models
paths:
  - "site/zenodo_rdm/**/models.py"
  - "site/zenodo_rdm/moderation/**"
---

Zenodo-RDM has no Alembic migrations of its own. The only SQLAlchemy models are
in `site/zenodo_rdm/moderation/models.py` (`LinkDomain`, `ModerationQuery`),
registered under `invenio_db.models` in `site/pyproject.toml`, so their tables
are created on a fresh instance via `invenio db create` (SQLAlchemy
`create_all`).

- Any change to a model's schema (new table, column, type, nullability, index,
  constraint, enum) does **not** migrate existing deployments automatically.
  Flag schema changes that don't state how the existing database will be
  updated (a deploy SQL step, a script, or a note in the deploy checklist).
- The moderation models are queried directly in request/service paths (e.g. the
  `LinkDomain.lookup_domain` subdomain match). Flag index or query changes that
  would make those lookups slow or wrong on a large table.
- Data in these tables is operational (spam/link moderation). Don't suggest
  fixtures or vocabulary-style migration recipes for them; they aren't loaded
  from `app_data/`.
- Model modules other than the moderation one must still be registered under
  `invenio_db.models` in `site/pyproject.toml` or their tables won't be created.
