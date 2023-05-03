##############
#
# Initial notes, read first.
#
# -  To be able to see deposits (with admin user), the owner of records must be hardcoded to the admin user id.
#
##############

# Clear DB
# Only run if DB has data.
invenio shell --no-term-title -c "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"

# NOTE: db destroy is not needed since DB keeps being created
#       Just need to drop all tables from it.
invenio db drop --yes-i-know
invenio index destroy --force --yes-i-know

# NOTE: This one doesn't purge all the indexer queues (e.g. `records`)...
#       We need a new command to do so, using the indexer registry?
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

# Backup and drop FK/PK/unique constraints and indices

# Run migration
python -m zenodo_rdm.migrator site/zenodo_rdm/migrator/streams.yaml

# Restore FK/PK/unique constraints and indices

# Update ID sequences in DB
# This is developed programatically, not need to run it manually.
<<com
psql -h <host> -U zenodo -d zenodo
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
