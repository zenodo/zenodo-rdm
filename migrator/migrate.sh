#!/bin/bash

# Clear DB, indices, Redis, and RabbitMQ
invenio db drop --yes-i-know
invenio index destroy --force --yes-i-know
invenio shell --no-term-title -c "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"
invenio index queue init purge --all-queues

# Create DB tables, files locations, and search indices
invenio db create
# NOTE: Important that this is the first location (PK: 1), so that bucket FK references work
invenio files location create 'eos' "root://eosmedia.cern.ch//eos/media/zenodo/prod/data/"
# NOTE: We set app instance path to allow for upload on test infra. Should be removed and instead use `eos` as default
invenio files location create --default 'default-location' $(invenio shell --no-term-title -c "print(app.instance_path)")'/data'
invenio index init --force
invenio rdm-records custom-fields init
invenio communities custom-fields init

# Migration target database
DB_URI="service=zenodo-target"

# Backup FK/PK/unique constraints
psql $DB_URI --tuples-only --quiet -f scripts/gen_create_constraints.sql > scripts/create_constraints.sql
psql $DB_URI --tuples-only --quiet -f scripts/gen_delete_constraints.sql > scripts/delete_constraints.sql
# Drop constraints
psql $DB_URI -f scripts/delete_constraints.sql

# Backup indices
psql $DB_URI --tuples-only --quiet -f scripts/gen_create_indices.sql > scripts/create_indices.sql
psql $DB_URI --tuples-only --quiet -f scripts/gen_drop_indices.sql > scripts/drop_indices.sql
# Drop indices
psql $DB_URI -f scripts/drop_indices.sql

# Import CSV and binary dumps

# Vocabularies
pv dumps/affiliation_metadata.csv | psql $DB_URI -c 'COPY affiliation_metadata (id, pid, json, created, updated, version_id) FROM STDIN (FORMAT csv);'
pv dumps/name_metadata.bin | psql $DB_URI -c 'COPY name_metadata (id, created, updated, pid, json, version_id) FROM STDIN (FORMAT binary);'
pv dumps/funder_metadata.csv | psql $DB_URI -c 'COPY funder_metadata (id, pid, json, created, updated, version_id) FROM STDIN (FORMAT csv);'
pv dumps/award_metadata.csv | psql $DB_URI -c 'COPY award_metadata (id, pid, json, created, updated, version_id) FROM STDIN (FORMAT csv);'

# OAuth
pv dumps/oauthclient_remoteaccount.bin | psql $DB_URI -c "COPY oauthclient_remoteaccount (id, user_id, client_id, extra_data, created, updated) FROM STDIN (FORMAT binary);"
pv dumps/oauthclient_remotetoken.bin | psql $DB_URI -c "COPY oauthclient_remotetoken (id_remote_account, token_type, access_token, secret, created, updated) FROM STDIN (FORMAT binary);"

# GitHub-related
pv dumps/webhooks_events.bin.gz | gzip -dc | psql $DB_URI -c "COPY webhooks_events (id, created, updated, receiver_id, user_id, payload, payload_headers, response, response_headers, response_code) FROM STDIN (FORMAT binary);"
pv dumps/github_repositories.bin | psql $DB_URI -c "COPY github_repositories (id, created, updated, github_id, name, user_id, hook) FROM STDIN (FORMAT binary);"

# Files
pv dumps/files_files.bin | psql $DB_URI -c "COPY files_files (id, created, updated, uri, storage_class, size, checksum, readable, writable, last_check_at, last_check) FROM STDIN (FORMAT binary);"
pv dumps/files_bucket.bin | psql $DB_URI -c "COPY files_bucket (id, created, updated, default_location, default_storage_class, size, quota_size, max_file_size, locked, deleted) FROM STDIN (FORMAT binary);"
pv dumps/files_object.bin | psql $DB_URI -c "COPY files_object (version_id, created, updated, key, bucket_id, file_id, _mimetype, is_head) FROM STDIN (FORMAT binary);"

# Run migration
python -m zenodo_rdm_migrator "streams-prod.yaml"

# Restore FK/PK/unique constraints and indices
psql $DB_URI -f scripts/create_constraints.sql
psql $DB_URI -f scripts/create_indices.sql

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
from invenio_rdm_records.proxies import current_rdm_records_service

# Commented out but left these here in case of urgent need
# affs_service = current_service_registry.get("affiliations")
# affs_service.rebuild_index(identity=system_identity)
# names_service = current_service_registry.get("names")
# names_service.rebuild_index(identity=system_identity)
# funders_service = current_service_registry.get("funders")
# funders_service.rebuild_index(identity=system_identity)
# awards_service = current_service_registry.get("awards")
# awards_service.rebuild_index(identity=system_identity)
# vocab_service = current_service_registry.get("vocabularies")
# vocab_service.rebuild_index(identity=system_identity)
# subj_service = current_service_registry.get("subjects")
# subj_service.rebuild_index(identity=system_identity)

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

# Spawn an appropriate number of worker tasks to process bulk indexing queues
<<com
import itertools
from invenio_indexer.proxies import current_indexer_registry
from invenio_indexer.tasks import process_bulk_queue
from celery import current_app as current_celery_app

channel = current_celery_app.connection().channel()
indexers = current_indexer_registry.all()

queues = {}

for name, indexer in indexers.items():
    queue = indexer.mq_queue.bind(channel)
    _, num_messages, _ = queue.queue_declare()
    queues[name] = num_messages

# We cycle, to make sure there's equally distributed consumption from the queues
for name in itertools.cycle(queues.keys()):
    if queues[name] > 0:
        process_bulk_queue.delay(indexer_name=name)
        queues[name] -= 10_000

    if all(v <= 0 for v in queues.values()):
        break
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
