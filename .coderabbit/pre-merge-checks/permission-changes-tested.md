---
id: permission-changes-tested
name: Permission changes are tested
mode: warning
report: platform
paths:
  - "site/zenodo_rdm/permissions.py"
  - "site/zenodo_rdm/generators.py"
  - "site/zenodo_rdm/legacy/tokens.py"
  - "site/tests/**"
---

Pass when the PR doesn't change the permission policies or generators in
`site/zenodo_rdm/permissions.py` or `site/zenodo_rdm/generators.py`.

If it does, pass only when the PR also adds or updates tests under
`site/tests/` that exercise each changed action, with at least one identity
that should be allowed and one that should be denied.

Fail otherwise. In the failure message, list the changed actions and say who
gains or loses access through each one.
