---
id: license-headers
name: License headers present
mode: warning
report: platform
paths:
  - "site/zenodo_rdm/**/*.py"
  - "site/tests/**/*.py"
  - "legacy/zenodo_legacy/**/*.py"
  - "legacy/tests/**/*.py"
  - "migrator/zenodo_rdm_migrator/**/*.py"
  - "migrator/tests/**/*.py"
  - "assets/**/*.js"
  - "site/zenodo_rdm/assets/**/*.js"
---

Pass when every **newly added** file in scope starts with the project SPDX
license header. Python uses `#` comment lines and JS uses `//` comment lines:

```
SPDX-FileCopyrightText: YYYY CERN
SPDX-License-Identifier: GPL-3.0-or-later
```

Files with additional copyright holders list them as extra
`SPDX-FileCopyrightText` lines before the `SPDX-License-Identifier` line.

Fail and list the new files whose header is missing. Don't fail on modified
files whose copyright year wasn't extended; mention them as a note instead.
