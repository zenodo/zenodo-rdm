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
  Both Invenio-CLI and the `wipe_recreate` script will create one user, which
  should not be there to avoid _id_ clashes (namely, `id=1`). To prevent it,
  create an empty `users.yaml` file in the instance `app_data` folder.

```console
invenio shell --no-term-title -c "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"
invenio db drop --yes-i-know
invenio index destroy --force --yes-i-know
invenio index queue init purge
invenio db create
invenio files location create --default 'default-location'  $(pipenv run invenio shell --no-term-title -c "print(app.instance_path)")'/data'
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

## Run!

- Run the dataset to DB migration:

```shell
python -m zenodo_rdm.migrator /path/to/streams.yaml
```

- Once it has finished, run the re-indexing. Note that this step will strain your CPU rendering your laptop almost useless. In a `invenio-cli pyshell` run:

```python
# You might want to first run users, then rebuild index.
# Then run records and rebuild its index.
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_users_resources.proxies import current_users_service
current_users_service.rebuild_index(identity=system_identity)
current_rdm_records_service.rebuild_index(identity=system_identity)
```

- When the workers have no longer any tasks to run, in the _pyshell_ run:

```python
current_users_service.indexer.refresh()
current_rdm_records_service.indexer.refresh()
```
