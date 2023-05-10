# ZenodoRDM migrator

How to execute a migration (Zenodo legacy to RDM)

## Pre-requisites

- Have a ZenodoRDM instance up and running, for example in OpenShift. However,
  note that some services such as RabbitMQ and Redis will crash with default
  resources due to OOM errors. For that you can deploy locally ZenodoRDM,
  connecting to a remote DB and OpenSearch cluster. You will need to set the
  following configuration in your `invenio.cfg` file:

```cfg
# This means that you will run locally the web and worker nodes, and connect
# to remote instances of DB, OpenSearch and Sentry.
# logging
SENTRY_DSN="https://secret12345abcde@locahost.sentry/3"
LOGGING_SENTRY_CELERY = True
LOGGING_SENTRY_LEVEL = "WARNING"
SENTRY_ENVIRONMENT = "qa"

# search
SEARCH_INDEX_PREFIX = "zenodo-"
SEARCH_HOSTS=[{'host': 'localhost', 'url_prefix': '/es', 'timeout': 30, 'port': 443, 'use_ssl': True, 'verify_certs': True, 'http_auth':('zenodo', 'password')}]

# db
SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://zenodo:zenodo@localhost:5432/zenodo"
```

- Remove all previous data, but leave (or recreate) vocabularies and fixtures.
  Note that you **MUST NOT** populate communities fixtures if you want to use
  the communities stream as you might have clashes on communities slug names.
  Both Invenio-CLI and the `wipe_recreate` script will create one user, which
  should not be there to avoid _id_ clashes (namely, `id=1`). To prevent it,
  create an empty `users.yaml` file in the instance `app_data` folder.

```console
# If on OpenShift
# bash -l
invenio shell --no-term-title -c "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"
invenio db drop --yes-i-know
invenio index destroy --force --yes-i-know
invenio index queue init purge
invenio db create
invenio files location create --default 'default-location' /opt/invenio/var/instance/data
invenio roles create admin
invenio access allow superuser-access role admin
invenio index init --force
invenio rdm-records custom-fields init
invenio communities custom-fields init
invenio rdm-records fixtures
invenio vocabularies import -v names -f ./app_data/vocabularies-future.yaml  # zenodo specific names
```

- Stop redis, rabbitmq, web and worker nodes on the PaaS project. This step
  is not strictly necessary. However, it will help spot misconfigurations and
  hard to spot issues.

- Fetch the datasets. For sandbox, they are available in the QA builder node
  in the `/migration` folder.

- Configure your `streams.yaml` file, you can see an example in this folder.
  You will need to run in a invenio shell the `site.zenodo_rdm.migrator.utils.dump_communities` method so that
  the `streams.yaml` is populated with the `communities_cache` i.e a map between
  communities slug names to communities ids.

## Run!

- Run the dataset to DB migration:

```shell
python -m zenodo_rdm.migrator /path/to/streams.yaml
```

```bash
# Manual COPY ...
export DB_URI=${SQLALCHEMY_DATABASE_URI}
cat rdm_records_metadata.csv | psql $DB_URI -c "COPY rdm_records_metadata (id, json, created, updated, version_id, index, bucket_id, parent_id) FROM STDIN (FORMAT csv);"

pv pidstore_pid.csv | psql $DB_URI -c "COPY pidstore_pid (id, pid_type, pid_value, status, object_type, object_uuid, created, updated) FROM STDIN (FORMAT csv);"
pv rdm_parents_metadata.csv | psql $DB_URI -c "COPY rdm_parents_metadata (id, json, created, updated, version_id) FROM STDIN (FORMAT csv);"
pv rdm_records_metadata.csv | psql $DB_URI -c "COPY rdm_records_metadata (id, json, created, updated, version_id, index, bucket_id, parent_id) FROM STDIN (FORMAT csv);"
pv rdm_parents_community.csv | psql $DB_URI -c "COPY rdm_parents_community (community_id, record_id, request_id) FROM STDIN (FORMAT csv);"
pv rdm_versions_state.csv | psql $DB_URI -c "COPY rdm_versions_state (latest_index, parent_id, latest_id, next_draft_id) FROM STDIN (FORMAT csv);"
```

- Once it has finished, run the re-indexing. Note that this step will strain your CPU rendering your laptop almost useless. In a `invenio-cli pyshell` run:

```python
# You might want to first run users, then rebuild index.
# Then run records and rebuild its index.
from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_users_resources.proxies import current_users_service
# Re-index users
current_users_service.rebuild_index(identity=system_identity)
# Re-index communities and members **if communities stream was used to populate communities**
current_communities.service.rebuild_index(identity=system_identity)
current_communities.service.members.rebuild_index(identity=system_identity)
# Re-index records
current_rdm_records_service.rebuild_index(identity=system_identity)
```

- When the workers have no longer any tasks to run, in the _pyshell_ run:

```python
current_users_service.indexer.refresh()
current_communities.service.indexer.refresh()
current_communities.service.members.indexer.refresh()
current_rdm_records_service.indexer.refresh()
```

or if memory is an issue then you can generate the index batches with the code below

```python
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_db import db

model_cls = current_rdm_records_service.record_cls.model_cls
records = db.session.query(model_cls.id).filter(
    model_cls.is_deleted == False,
).yield_per(1000)

current_rdm_records_service.indexer.bulk_index((rec.id for rec in records))
```

- If you populate communities via the communities stream and not fixtures and a specific
  user doesn't seem to have the correct roles when visiting a community, then you might
  need to run the `site.zenodo_rdm.migrator.utils.invalidate_user_community_roles_cache`
  so users community roles are being re-cached.

## Generating dumps

In order to generate the dumps used by the migrator, you need access to a legacy Zenodo
database with either live data or a snapshot.

In `zenodo-rdm/site/zenodo_rdm/migrator/extract.py`, you'll find the SQL queries for
dumping the data needed for each of the migration streams. You can run these queries
directly on the legacy database, in the following manner:

```shell
# NOTE: Adjust the connection string as necessary
DB_URI="postgresql://zenodo@zenodo-legacy-db-host:5432/zenodo"

# Users, ~30min
psql $DB_URI -f scripts/users_dump.sql | sed 's/\\\\/\\/g' | gzip -c > "dumps/users-$(date -I).jsonl.gz"
# Communities, ~5min
psql $DB_URI -f scripts/communities_dump.sql | sed 's/\\\\/\\/g' | gzip -c > "dumps/communities-$(date -I).jsonl.gz"
# Community record inclusion requests, ~10min
psql $DB_URI -f scripts/requests_dump.sql | sed 's/\\\\/\\/g' | gzip -c > "dumps/requests-$(date -I).jsonl.gz"
# Records, ~2-3h
psql $DB_URI -f scripts/records_dump.sql | sed 's/\\\\/\\/g' | gzip -c > "dumps/records-$(date -I).jsonl.gz"
# Deposits/drafts, ~30min
psql $DB_URI -f scripts/deposits_dump.sql | sed 's/\\\\/\\/g' | gzip -c > "dumps/deposits-$(date -I).jsonl.gz"


# For dumping files we use a different style, since we're not filtering anything:

# File instances, ~10min
psql $DB_URI -f scripts/files_files_dump.sql | gzip -c > "dumps/files_files-$(date -I).jsonl.gz"
# Buckets, ~1min
psql $DB_URI -f scripts/files_bucket_dump.sql | gzip -c > "dumps/files_bucket-$(date -I).dump.gz"
# File object versions, ~3min
psql $DB_URI -f scripts/files_object_dump.sql | gzip -c > "dumps/files_object-$(date -I).dump.gz"
```
