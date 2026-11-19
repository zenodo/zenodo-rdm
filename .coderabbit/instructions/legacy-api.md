---
id: legacy-api
name: Legacy REST API and compatibility layer
paths:
  - "site/zenodo_rdm/legacy/**"
  - "site/zenodo_rdm/api.py"
  - "site/zenodo_rdm/resources.py"
  - "site/zenodo_rdm/serializers/**"
  - "site/zenodo_rdm/queryparser.py"
  - "site/zenodo_rdm/facets.py"
  - "site/zenodo_rdm/redirector.py"
  - "site/zenodo_rdm/tokens.py"
  - "legacy/zenodo_legacy/**"
  - "site/tests/legacy/**"
---

`site/zenodo_rdm/legacy/` reimplements the old Zenodo REST API (deposits,
files, records) on top of InvenioRDM for backward compatibility. It is backed
by `ZenodoRDMDraft` / `ZenodoRDMRecord` (`site/zenodo_rdm/api.py`) and wired up
through the `invenio_base.api_blueprints` and `invenio_oauth2server.scopes`
entry points in `site/pyproject.toml`.

Review for:

- **Wire compatibility.** Legacy serializers (`legacy/serializers/`,
  `serializers/`) must stay byte-for-byte compatible with the old Zenodo API.
  Flag renamed fields, changed defaults, reordered keys that clients parse
  positionally, and date/identifier formatting changes. Every change is a
  breaking change for an existing client.
- **Legacy deserializers** (`legacy/deserializers/`) must accept the old
  payload shapes and map them onto RDM metadata. Tolerate missing and
  deprecated fields rather than raising; no unguarded `[0]` or `["key"]` on
  optional input.
- **Legacy search.** `queryparser.py` (`ZENODO_LEGACY_SEARCH_MAP`), `facets.py`
  and the legacy sort options map old query parameters and facets onto the RDM
  search. A change there can silently break old search URLs; check the mapping
  preserves legacy semantics (query names, sort keys, facet ids).
- **Tokens and scopes.** `legacy/tokens.py` defines `LegacySecretLinkNeed`, and
  `legacy/scopes.py` the deposit OAuth2 scopes. Granting a legacy token must not
  bypass record-level permissions; check the need is exercised through the
  permission policy, not trusted on its own.
- **Legacy request types.** `LegacyRecordUpgrade` and `CommunityManageRecord`
  carry user intent from the old system. Check their action permissions,
  notification builders and templates, and that they handle missing/deleted
  records.
- **Redirects.** `redirector.py` keeps old Zenodo URLs (records, badges, DOI
  redirects) resolving. A removed or re-keyed redirect breaks bookmarked links;
  flag it and ask for the old→new mapping to be stated.
- `legacy/zenodo_legacy/` maps legacy funder/license identifiers onto the RDM
  vocabularies. Changes to those mappings change how old records resolve; keep
  them consistent with `app_data/`.
- Tests for a changed serializer/deserializer/mapping go under
  `site/tests/legacy/` with a representative legacy payload.
