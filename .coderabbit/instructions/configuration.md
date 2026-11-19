---
id: configuration-and-deployment
name: Instance configuration, dependencies and deployment
paths:
  - "invenio.cfg"
  - "site/zenodo_rdm/config.py"
  - "site/zenodo_rdm/**/config.py"
  - "pyproject.toml"
  - "site/pyproject.toml"
  - "legacy/pyproject.toml"
  - "Dockerfile"
  - "docker/**"
  - "docker-compose*.yml"
  - "docker-services.yml"
  - ".github/workflows/**"
---

- `invenio.cfg` is shared by local development and deployments. Production
  values come from `INVENIO_*` environment variables. Flag real secrets, tokens,
  passwords, hostnames or internal CERN endpoints added as literals. The
  existing `CHANGE_ME` / `"CHANGE ME"` / empty-string placeholders are
  intentional.
- `ZENODO_ENV` is one of `local`, `dev`, `qa`, `production`, and a lot of config
  is conditional on `IS_LOCAL_DEV` or the environment. Flag a change that
  silently behaves differently per environment without saying so.
- Changes to permission policies, record or file settings, OAI-PMH, DataCite/DOI
  minting, OpenAIRE sync, search, stats, or Celery beat schedules have
  production impact. Ask for the intended behaviour to be stated in the PR.
- Overriding an upstream config key: check that the name exists in the
  installed `invenio-*` version, since a typo silently has no effect, and that
  it isn't already set elsewhere in the file.
- Dependency changes in `pyproject.toml` must come with an updated `uv.lock`
  (CI runs `uv sync --locked`; the Docker build runs `uv export --frozen`). JS
  dependency changes need an updated `pnpm-lock.yaml` (the Docker build runs
  `pnpm install --frozen-lockfile`). Upgrades of `invenio-app-rdm` or other
  `invenio-*` packages are major-version sensitive. Ask whether upstream upgrade
  notes or migrations apply.
- `invenio-app-rdm`, `invenio-records-resources`, `invenio-accounts`,
  `invenio-stats` and `invenio-jobs` are currently pinned to git branches/forks
  (see `[tool.uv.sources]`). Flag accidental reverts to a released version or a
  bump that drops a local fix.
- Python targets 3.14 (see CI and the Docker base images). Don't suggest
  compatibility shims for older versions.
- Dockerfile/compose: pin base image versions, don't bake in secrets, and keep
  layer order cache-friendly. The final image is `python:3.14-slim-trixie` and
  must stay on the same Python/Debian release as the build base image.
