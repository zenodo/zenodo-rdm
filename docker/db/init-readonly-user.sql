-- Create a read-only user
CREATE USER zenodo_ro WITH PASSWORD 'zenodo_ro';
-- Cap replica reads. Set on the primary; role settings replicate to
-- the standby. For an already-initialized db, run these two statements once manually.
ALTER ROLE zenodo_ro SET statement_timeout = '30s';
ALTER ROLE zenodo_ro SET idle_in_transaction_session_timeout = '60s';
-- Grant connect access to the database
GRANT CONNECT ON DATABASE zenodo TO zenodo_ro;
-- Grant usage on the public schema
GRANT USAGE ON SCHEMA public TO zenodo_ro;
-- Grant read access to all tables in the public schema
GRANT pg_read_all_data TO zenodo_ro;
