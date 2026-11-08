-- Create test database and user with superuser for full test control
-- This runs after init.sql in the same PostgreSQL instance

CREATE DATABASE workbench_test;
CREATE USER workbench_test WITH PASSWORD 'test_password' SUPERUSER;
GRANT ALL PRIVILEGES ON DATABASE workbench_test TO workbench_test;
