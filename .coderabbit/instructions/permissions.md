---
id: permissions
name: Permissions and access generators
paths:
  - "site/zenodo_rdm/permissions.py"
  - "site/zenodo_rdm/generators.py"
  - "site/zenodo_rdm/legacy/tokens.py"
  - "site/zenodo_rdm/request_policies.py"
  - "site/zenodo_rdm/legacy/requests/**"
  - "site/zenodo_rdm/subcommunities/**"
---

These files decide who can see and change records at Zenodo. Restricted and
embargoed content is a real data-leak risk, so review this area strictly.

- Policies are lists of `Generator`s per action (`can_read`, `can_update_draft`,
  `can_publish`, `can_manage_files`, …). For each changed action, state who
  **gains** access and who **loses** it. Treat any widening of `can_read`,
  `can_read_files`, `can_search` or `can_manage` as high-risk and call it out
  explicitly. The record policy lives in `ZenodoRDMRecordPermissionPolicy` and
  the community policy in `ZenodoCommunityPermissionPolicy` (both in
  `permissions.py`).
- A generator must implement `needs()` and, if used in search, `query_filter()`
  consistently. A generator that grants a need without the matching query
  filter, or the other way round, makes search results disagree with
  record-level access.
- `excludes()` is rarely the right tool. Check it isn't used to "fix" a
  `needs()` bug.
- Admins usually hold `superuser-access`, which bypasses most checks. Code that
  must constrain admins has to say so explicitly. Don't let a refactor drop
  that.
- `SystemProcess` belongs only on actions the jobs, tasks or the migrator
  perform.
- New `invenio_access` actions must be registered as entry points in
  `site/pyproject.toml` (see `media_files_management_action`,
  `manage_external_doi_files_action`, `orcha_access_action`), and any role they
  rely on must exist (fixtures or an upgrade step).
- The legacy layer defines its own token need (`LegacySecretLinkNeed` in
  `legacy/tokens.py`) and request types (`LegacyRecordUpgrade`,
  `CommunityManageRecord`). Request types need permissions for every request
  action (`create`, `submit`, `accept`, `decline`, `cancel`, `expire`, comment)
  and matching notification builders and templates.
- Ask for tests that cover both the allowed and the denied identity for every
  changed action.
