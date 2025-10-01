-- =============================================================================
-- BlingAuto API - PostgreSQL Database Initialization Script
-- Creates database, user, and sets up initial configuration
-- =============================================================================

-- This script runs automatically when PostgreSQL container starts
-- via docker-entrypoint-initdb.d

-- Database and user are already created by POSTGRES_DB, POSTGRES_USER environment variables
-- This script can be used for additional initialization

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Set timezone to UTC
ALTER DATABASE blingauto SET timezone TO 'UTC';

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON DATABASE blingauto TO blingauto_user;

-- Connection limits (optional, adjust based on needs)
-- ALTER ROLE blingauto_user CONNECTION LIMIT 100;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'BlingAuto database initialized successfully';
    RAISE NOTICE 'Extensions: uuid-ossp, pg_trgm';
    RAISE NOTICE 'Timezone: UTC';
END $$;
