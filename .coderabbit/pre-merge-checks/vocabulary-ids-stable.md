---
id: vocabulary-ids-stable
name: Vocabulary id changes have a migration
mode: warning
report: platform
paths:
  - "app_data/vocabularies/**"
  - "app_data/vocabularies.yaml"
  - "app_data/vocabularies-future.yaml"
---

Published records reference vocabulary ids, so renaming or removing an existing
entry's `id` orphans them unless the records are migrated.

Pass when the PR only adds new entries or edits non-id fields (titles, aliases,
props, tags) of existing ones.

When an existing `id` is renamed or removed, pass only if the PR description
contains a migration recipe for existing records: the old-to-new id mapping and
how it will be applied (script, command or job). Fail otherwise, listing the
affected ids.

Also fail when the PR adds an `id` that already exists in the same file.
