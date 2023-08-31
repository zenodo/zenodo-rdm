-- From https://www.postgresql.org/message-id/flat/877em2racj.fsf%40gmail.com#36a9eba4b16b8172e379b2a19f403939
CREATE TABLE rdm_index_backup AS
SELECT *
FROM pg_indexes
WHERE
  schemaname = 'public'
  AND tablename IN (
    -- files
    'files_files',
    'files_bucket',
    'files_object',
    -- users
    'accounts_user',
    'accounts_user_login_information',
    'accounts_user_session_activity',
    'oauth2server_token',
    'accounts_useridentity',
    -- communities
    'communities_metadata',
    'communities_members',
    'communities_featured',
    'oaiserver_set',
    -- records
    'rdm_records_metadata',
    'rdm_parents_metadata',
    'rdm_parents_community',
    'rdm_drafts_metadata',
    'rdm_versions_state',
    'rdm_records_files',
    'rdm_drafts_files',
    'pidstore_pid',
    -- requests
    'request_metadata',
    -- github
    'webhooks_events',
    'github_repositories',
    'github_releases'
  );
