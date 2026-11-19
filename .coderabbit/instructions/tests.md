---
id: tests
name: Test suite
paths:
  - "site/tests/**"
  - "site/conftest.py"
  - "legacy/tests/**"
  - "migrator/tests/**"
---

- Tests run with `pytest-invenio` against real PostgreSQL and OpenSearch
  (plus RabbitMQ/Redis) via `docker-services-cli` (`site/run-tests.sh`). Prefer
  the shared fixtures in `site/tests/conftest.py` (app config, users/identities,
  vocabularies, communities, minimal records, `running_app`, `publish_record`)
  over building app state by hand.
- External services (DataCite, OpenAIRE, GitHub, ORCID, Zammad, Software
  Heritage, LDAP/Keycloak) must be faked or mocked. See
  `site/tests/fake_datacite_client.py`. A test that reaches the network is a
  bug.
- After writes, tests that query search must refresh the index (for example
  `Record.index.refresh()`), or they will be flaky.
- Permission changes need both a positive and a negative assertion.
- Docstring examples are run as doctests (`--doctest-modules`); keep them
  accurate. Formatting/import-order/docstring checks run through the same
  pytest invocation (`--isort --pydocstyle`), so CI fails on violations.
- Name tests by behaviour and keep them independent. No reliance on test order
  or on state left by another module's fixtures.
