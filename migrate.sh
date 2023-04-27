# Clear DB
# Only run if DB has data.
invenio shell --no-term-title -c "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"

# NOTE: db destroy is not needed since DB keeps being created
#       Just need to drop all tables from it.
invenio db drop --yes-i-know
invenio index destroy --force --yes-i-know
invenio index queue init purge

# Recreate
# --------
# NOTE: db init is not needed since DB keeps being created
#       Just need to create all tables from it.
invenio db create
# TODO: add back when pipenv access problem is fixed
#invenio files location create --default 'default-location'  $(pipenv run invenio shell --no-term-title -c "print(app.instance_path)")'/data'
invenio files location create --default 'default-location' /opt/invenio/var/instance/data
invenio index init --force
invenio rdm-records custom-fields init
invenio communities custom-fields init

# Run migration
python -m zenodo_rdm.migrator site/zenodo_rdm/migrator/streams.yaml

# Update ID sequences in DB
psql -h <host> -U zenodo -d zenodo
<<com
SELECT MAX(id) from accounts_user;
ALTER SEQUENCE ALTER SEQUENCE accounts_user_id_seq RESTART WITH {ID}; # Insert ID from before
com

# Fixtures 
invenio rdm-records fixtures 
invenio vocabularies import -v names -f ./app_data/vocabularies-future.yaml  # zenodo specific names

# Reindex records and communities
invenio rdm-records rebuild-index
invenio communities rebuild-index

# Reindex users
# Open an invenio shell and run the command:
<<com
from invenio_access.permissions import system_identity
from invenio_users_resources.proxies import current_users_service

current_users_service.rebuild_index(identity=system_identity)
com

# When finished indexing, refresh the index
<<com
from invenio_users_resources.proxies import current_users_service

current_users_service.indexer.refresh()
com

# invenio roles create admin
# invenio access allow superuser-access role admin