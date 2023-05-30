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
invenio files location create --default 'default-location'  $(pipenv run invenio shell --no-term-title -c "print(app.instance_path)")'/data'
invenio index init --force
invenio rdm-records custom-fields init
invenio communities custom-fields init

# Script base path
script_path=$( cd -- "$(dirname "$0")" && pwd )
migrator_path=$script_path/site/zenodo_rdm/migrator
migrator_scripts_folder_path=$migrator_path/scripts

# Backup FK/PK/unique constraints
DB_URI="postgresql://zenodo:zenodo@localhost/zenodo"

psql $DB_URI --tuples-only --quiet -f $migrator_scripts_folder_path/gen_create_constraints.sql > $migrator_scripts_folder_path/create_constraints.sql
psql $DB_URI --tuples-only --quiet -f $migrator_scripts_folder_path/gen_delete_constraints.sql > $migrator_scripts_folder_path/delete_constraints.sql

# Drop constraints
psql $DB_URI -f $migrator_scripts_folder_path/delete_constraints.sql

# Backup indices
psql $DB_URI -f $migrator_scripts_folder_path/backup_indices.sql
psql $DB_URI -f $migrator_scripts_folder_path/drop_indices.sql


# Run migration
# python -m zenodo_rdm.migrator site/zenodo_rdm/migrator/streams.yaml
python -m zenodo_rdm.migrator $migrator_path/streams.yaml

# TODO: These should be fixed in the legacy/source
# Apply various consistency fixes


# Restore FK/PK/unique constraints and indices
psql $DB_URI -f $migrator_scripts_folder_path/create_constraints.sql
psql $DB_URI -f $migrator_scripts_folder_path/restore_indices.sql

# Update ID sequences in DB
psql $DB_URI -f $migrator_scripts_folder_path/update_sequences.sql

# Fixtures
invenio rdm-records fixtures
invenio vocabularies import -v names -f $script_path/app_data/vocabularies-future.yaml  # zenodo specific names

# TODO: Load these via regular migration streams
# Load awards via COPY
pv awards.csv | psql $DB_URI -c "COPY award_metadata (id, pid, json, created, updated, version_id) FROM STDIN (FORMAT csv);"

# Truncate any previous funders (e.g. from fixtures), and load funders via copy
psql $DB_URI -c "truncate funder_metadata"
pv funders.csv | psql $DB_URI -c "COPY funder_metadata (id, pid, json, created, updated, version_id) FROM STDIN (FORMAT csv);"

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

# Add admin users (Pablo, Alex, Zach, Manuel)
sh $migrator_scripts_folder_path/add_admins.sh