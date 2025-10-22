-- PostgreSQL initialization script for NikNotes
-- This script runs when the PostgreSQL container is first created

-- Ensure the database is created (docker-compose already does this)
-- CREATE DATABASE IF NOT EXISTS is not valid in PostgreSQL, so we use psql commands

-- Set timezone
SET timezone = 'UTC';

-- Enable extensions if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges (already done by docker-compose)
GRANT ALL PRIVILEGES ON DATABASE niknotes_db TO niknotes_user;

-- Connect to the database
\c niknotes_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO niknotes_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO niknotes_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO niknotes_user;

-- Performance settings are configured in docker-compose.yml via command-line parameters
-- No ALTER SYSTEM commands needed here as they would conflict with startup settings

-- Success message
SELECT 'NikNotes PostgreSQL database initialized successfully!' as status;
