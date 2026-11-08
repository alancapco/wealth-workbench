-- Create test database and user
-- This runs after init.sql in the same PostgreSQL instance

CREATE DATABASE workbench_test;
CREATE USER workbench_test WITH PASSWORD 'test_password';
GRANT ALL PRIVILEGES ON DATABASE workbench_test TO workbench_test;

-- Grant schema permissions
\c workbench_test
GRANT ALL ON SCHEMA public TO workbench_test;
GRANT ALL ON ALL TABLES IN SCHEMA public TO workbench_test;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO workbench_test;
