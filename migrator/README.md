# ZenodoRDM migrator

How to execute a migration (Zenodo legacy to InvenioRDM)

## Pre-requisites

### Configuration

Have a ZenodoRDM instance up and running, for example in OpenShift. However,
note that some services such as RabbitMQ and Redis will crash with default
resources due to OOM errors. For that you can deploy locally ZenodoRDM,
connecting to a remote DB and OpenSearch cluster. You will need to set the
following configuration in your `invenio.cfg` file:

```python
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

### Data fixtures

Remove all previous data, but leave (or recreate) vocabularies.

Note that you **MUST NOT** populate users, communities nor records fixtures if you want to
migrate these (i.e. user their streams). This is due to potential clashes on communities
slug names and pks.

Regarding users, note that both Invenio-CLI and the `wipe_recreate.sh` script will create
one user, which should not be there to avoid _id_ clashes (namely, `id=1`). To prevent it,
create an empty `users.yaml` file in the instance `app_data` folder. Note that until
119c3cb5cc0e155fad62ccfed4d6366e184989ab (5th of May) is released, a user will also be
created automatically by the fixtures engine and it needs to be removed manually from the
database.

```shell
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
# TODO: add funders
# TODO: add awards
```

1. Stop redis, rabbitmq, web and worker nodes on the PaaS project. This step
  is not strictly necessary. However, it will help spot misconfigurations and
  hard to spot issues.

2. Fetch the datasets. For sandbox, they are available in the QA builder node
  in the `/migration` folder.

## Migrate

### Configure the streams

Configure your `streams.yaml` file, you can see an example in this folder.

**Prepopulate communities cache**

To prepopulate the communities cache with a mapping between slugs and uuids you
need to run in a invenio shell the `site.zenodo_rdm.migrator.utils.dump_communities`.
This function will read the `streams.yaml` file to obtain the cache file path
and overwrite it with a map of the existing communities in the system.

**Run from existing data**

Once you have completed a migration run and you consider that the data of a specific
stream is correct, you can avoid running the extract and transform steps. This way,
in case a stream fails, previous ones only need to load the data. In order to do so:

1. Move the csv files to the `<data_dir>/<stream_name>` directory. You can find that
information in the streams.yaml file.
2. Edit the corresponding streams in the `streams.yaml` file. Remove the extract,
transform and load configuration. Set `existing_data: true`, for example:

```yaml
users:
  existing_data: True
```

**Versioning**

The records and drafts streams both contain the versions table generator. This tg gets is
input data from the shared "parents" cache. This means that is should only run once, after
all the modifications have been made and updated to the cache. That is why the "records"
stream has a `versioning: false` set in the load step.

This could be removed if the COPY statement would support UPSERT instead of INSERT
operations.

### Prepare SQL scripts

- Create drop and create constraints script:

```
TODO
```

- Create drop and create indices script:

```
TODO
```

### Run!

1. Drop constraints and indices to speed up insertions
2. Run the dataset to DB migration:

```shell
python -m zenodo_rdm_migrator /path/to/streams.yaml
```
3. Create constraints and indices
4. Once it has finished, run the re-indexing. Note that this step will strain your CPU rendering your laptop almost useless. In a `invenio-cli pyshell` run:

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

4. When the workers have no longer any tasks to run, in the _pyshell_ run:

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

# FIXME: add drafts
model_cls = current_rdm_records_service.record_cls.model_cls
records = db.session.query(model_cls.id).filter(
    model_cls.is_deleted == False,
).yield_per(1000)

current_rdm_records_service.indexer.bulk_index((rec.id for rec in records))
```

5. If you populate communities via the communities stream and not fixtures and a specific
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
psql $DB_URI -f scripts/users_dump.sql | sed 's/\\\\/\\/g' > "dumps/users.jsonl"
# Communities, ~5min
psql $DB_URI -f scripts/communities_dump.sql | sed 's/\\\\/\\/g' > "dumps/communities.jsonl"
# Community record inclusion requests, ~10min
psql $DB_URI -f scripts/requests_dump.sql | sed 's/\\\\/\\/g' > "dumps/requests.jsonl"
# Records, ~2-3h
psql $DB_URI -f scripts/records_dump.sql | sed 's/\\\\/\\/g' > "dumps/records.jsonl"
# Deposits/drafts, ~30min
psql $DB_URI -f scripts/deposits_dump.sql | sed 's/\\\\/\\/g' > "dumps/deposits.jsonl"
# Deleted records, ~3-4h
psql $DB_URI -f scripts/deleted_records_dump.sql | sed 's/\\\\/\\/g' > "dumps/deleted-records.jsonl"

# Oauth2 server clients
psql $DB_URI -f scripts/oauth2server_clients_dump.sql | sed 's/\\\\/\\/g' > "dumps/oauth2server-clients.jsonl"
# Oauth2 server tokens
psql $DB_URI -f scripts/oauth2server_tokens_dump.sql | sed 's/\\\\/\\/g' > "dumps/oauth2server-tokens.jsonl"

# NOTE: For OAuth client and files we use the CSV format, since we're not transforming anything
# Oauth-Client accounts
psql $DB_URI -f scripts/oauthclient_remoteaccount_dump.sql > "dumps/oauthclient_remoteaccount.bin"
# Oauth-Client tokens
psql $DB_URI -f scripts/oauthclient_remotetoken_dump.sql > "dumps/oauthclient_remotetoken.bin"
# File instances, ~10min
psql $DB_URI -f scripts/files_files_dump.sql > "dumps/files_files.bin"
# Buckets, ~1min
psql $DB_URI -f scripts/files_bucket_dump.sql > "dumps/files_bucket.bin"
# File object versions, ~3min
psql $DB_URI -f scripts/files_object_dump.sql > "dumps/files_object.bin"

# Webhook Events
psql $DB_URI -f scripts/webhook_events_dump.sql > "dumps/webhook_events.bin"
# GitHub repositories
psql $DB_URI -f scripts/github_repositories_dump.sql > "dumps/github_repositories.bin"
# GitHub releases
psql $DB_URI -f scripts/github_releases_dump.sql | sed 's/\\\\/\\/g' > "dumps/github_releases.jsonl"
```
