-- Initialize PostgreSQL database with TimescaleDB and pgvector extensions

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Note: The main application tables are created by SQLAlchemy
-- This file only sets up the PostgreSQL extensions

-- Grant all permissions to the user
-- (Table creation happens via SQLAlchemy in the backend)
