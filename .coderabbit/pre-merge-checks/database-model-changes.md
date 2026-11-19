---
id: database-model-changes
name: Database model changes have a migration plan
mode: warning
report: platform
paths:
  - "site/zenodo_rdm/**/models.py"
---

Zenodo-RDM has no Alembic migrations; the models in
`site/zenodo_rdm/moderation/models.py` are created on fresh installs via
`invenio db create` (`create_all`) and are not migrated automatically on
existing deployments.

Pass when the PR doesn't change the schema of a SQLAlchemy model in
`site/zenodo_rdm/**/models.py`.

If it adds, removes or alters a table, column, type, nullability, index,
constraint or enum, pass only when the PR states how existing databases will be
updated (a deploy SQL step, a script, or a note in the deploy checklist).

Fail otherwise, naming the model change and saying what's missing.
