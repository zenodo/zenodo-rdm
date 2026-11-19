---
id: vocabularies-fixtures
name: Vocabulary and fixture data
paths:
  - "app_data/**"
---

`app_data/vocabularies.yaml` and `app_data/vocabularies/*.yaml` (affiliations,
awards, description types, funders, licenses) are controlled vocabularies
loaded with `invenio rdm-records fixtures`; `app_data/vocabularies-future.yaml`
is loaded separately with `invenio vocabularies import -v names`. Their ids end
up in record metadata and in the search index.

- **Renaming or removing an existing `id` needs a migration recipe in the PR
  description** (the old-to-new mapping and how existing records get updated),
  because published records reference it. Renaming the title or adding an alias
  needs no migration.
- New entries must have a unique `id` within the file. Look for duplicates or
  near-duplicates (case, whitespace, acronym versus full name) of existing
  entries.
- Keep the file's existing structure: `title` per language (at least `en`),
  `props`, `tags`, aliases and hierarchy keys used by neighbouring entries. For
  hierarchical vocabularies, parents must exist.
- Award and funder entries must reference an existing funder id, and their
  identifiers (ROR, grant number, CORDIS/DOI) must be well-formed.
- `licenses.csv` is a flat import; keep its columns and id scheme consistent
  with how the license vocabulary is consumed.
- Fixtures only load into empty instances. For production, say in the PR how the
  change will be applied (an update command or job). Flag vocabulary PRs that
  don't mention it.
- `app_data/pages/*.html` are static legal/policy pages. Check links and avoid
  inline scripts.
- `known_file_formats.yaml` drives the file-format checks; keep its entries
  consistent with the checks that consume them.
