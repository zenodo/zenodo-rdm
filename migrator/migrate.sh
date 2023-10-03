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
invenio files location create --default 'default-location' $(invenio shell --no-term-title -c "print(app.instance_path)")'/data'
invenio index init --force
invenio rdm-records custom-fields init
invenio communities custom-fields init

# Script base path
script_path=$( cd -- "$(dirname "$0")" && pwd )

LEGACY_DB_URI="service=zenodo-legacy"
DB_URI="service=zenodo-dev"

# Backup FK/PK/unique constraints
psql $DB_URI --tuples-only --quiet -f scripts/gen_create_constraints.sql > scripts/create_constraints.sql
psql $DB_URI --tuples-only --quiet -f scripts/gen_delete_constraints.sql > scripts/delete_constraints.sql

# Drop constraints
psql $DB_URI -f scripts/delete_constraints.sql

# Backup indices
psql $DB_URI -f scripts/backup_indices.sql
psql $DB_URI -f scripts/drop_indices.sql

# Run migration
python -m zenodo_rdm_migrator "streams.yaml"

# TODO: These should be fixed in the legacy/source
# Apply various consistency fixes

# Import OAuthclient models
psql $DB_URI -f scripts/oauthclient_remoteaccount_dump.sql > "dumps/oauthclient_remoteaccount.bin"
psql $DB_URI -f scripts/oauthclient_remotetoken_dump.sql > "dumps/oauthclient_remotetoken.bin"
pv dumps/oauthclient_remoteaccount.bin | psql $DB_URI -c "COPY oauthclient_remoteaccount (id, user_id, client_id, extra_data, created, updated) FROM STDIN (FORMAT binary);"
pv dumps/oauthclient_remotetoken.bin | psql $DB_URI -c "COPY oauthclient_remotetoken (id_remote_account, token_type, access_token, secret, created, updated) FROM STDIN (FORMAT binary);"

# Restore FK/PK/unique constraints and indices
psql $DB_URI -f scripts/create_constraints.sql
psql $DB_URI -f scripts/restore_indices.sql

# Update ID sequences in DB
psql $DB_URI -f scripts/update_sequences.sql

# Create missing DB indices to speed up records indexing
psql $DB_URI -f scripts/create_missing_indices.sql

# Fixtures
invenio rdm-records fixtures

###########################################################
# Reindex records
# Vocabularies should be already in the cluster
<<com
###########################################################
# Taken from:
# invenio rdm-records rebuild-index

from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry
from invenio_rdm_recods.proxies import current_rdm_records_service

# Commented out but left these here in case of urgent need
#vocab_service = current_service_registry.get("vocabularies")
#vocab_service.rebuild_index(identity=system_identity)
#names_service = current_service_registry.get("names")
#names_service.rebuild_index(identity=system_identity)
#funders_service = current_service_registry.get("funders")
#funders_service.rebuild_index(identity=system_identity)
#awards_service = current_service_registry.get("awards")
#awards_service.rebuild_index(identity=system_identity)
#subj_service = current_service_registry.get("subjects")
#subj_service.rebuild_index(identity=system_identity)
#affs_service = current_service_registry.get("affiliations")
#affs_service.rebuild_index(identity=system_identity)

# Re-index record/drafts
current_rdm_records_service.rebuild_index(identity=system_identity)
com

###########################################################
# Reindex communities
invenio communities rebuild-index

###########################################################
# Reindex users, groups, members, archived invitations, requests, events
# Open an invenio shell and run the command:
<<com
from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_requests.proxies import current_events_service, current_requests_service
from invenio_rdm_recods.proxies import current_rdm_records_service
from invenio_users_resources.proxies import current_users_service, current_groups_service

# reindex users
current_users_service.rebuild_index(system_identity)

# reindex groups
current_groups_service.rebuild_index(system_identity)

# reindex members and archived invitations
current_communities.service.members.rebuild_index(system_identity)

# reindex requests
for req_meta in current_requests_service.record_cls.model_cls.query.all():
    request = current_requests_service.record_cls(req_meta.data, model=req_meta)
    if not request.is_deleted:
        current_requests_service.indexer.index(request)

# reindex requests events
for event_meta in current_events_service.record_cls.model_cls.query.all():
    event = current_events_service.record_cls(event_meta.data, model=event_meta)
    current_events_service.indexer.index(event)
com

# For anything above 10K, manually spawn `process_bulk_queue` to put the Celery workers to work
<<com
from invenio_communities.proxies import current_communities
from invenio_requests.proxies import current_events_service, current_requests_service
from invenio_rdm_recods.proxies import current_rdm_records_service
from invenio_users_resources.proxies import current_users_service, current_groups_service

# Records ~3.5M / 10k messages = 350
for _ in range(350):
    current_rdm_records_service.indexer.process_bulk_queue()
# Drafts ~500k / 10k messages = 50
for _ in range(50):
    current_rdm_records_service.draft_indexer.process_bulk_queue()
# Users: ~600k / 10k messages = 60
for _ in range(60):
    current_users_service.indexer.process_bulk_queue()
com

# When finished indexing, refresh the indices
<<com
from invenio_users_resources.proxies import current_users_service, current_groups_service
from invenio_communities.proxies import current_communities
from invenio_requests.proxies import current_events_service, current_requests_service

current_users_service.indexer.refresh()
current_groups_service.indexer.refresh()
current_communities.service.members.indexer.refresh()
current_requests_service.indexer.refresh()
current_events_service.indexer.refresh()
current_rdm_records_service.indexer.refresh()
com

# Add admin users (Alex, Zach, Manuel)
sh scripts/add_admins.sh
