-- Create a read-only user
CREATE USER zenodo_ro WITH PASSWORD 'zenodo_ro';
-- Grant connect access to the database
GRANT CONNECT ON DATABASE zenodo TO zenodo_ro;
-- Grant usage on the public schema
GRANT USAGE ON SCHEMA public TO zenodo_ro;
-- Grant read access to all tables in the public schema
GRANT pg_read_all_data TO zenodo_ro;
