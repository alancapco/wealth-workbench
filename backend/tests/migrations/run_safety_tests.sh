#!/usr/bin/env bash
# U-002 Migration Safety Test Runner
# Spins up disposable PostgreSQL container and runs migration tests

set -e

CONTAINER_NAME="rm-workbench-test-migrations"
POSTGRES_VERSION="15"
TEST_PORT="5433"
TEST_USER="test"
TEST_PASSWORD="test"
TEST_DB="test_migrations"

export TEST_DATABASE_URL="postgresql+asyncpg://${TEST_USER}:${TEST_PASSWORD}@localhost:${TEST_PORT}/${TEST_DB}"

echo "=== U-002 Migration Safety Test Runner ==="
echo ""
echo "This script:"
echo "  1. Starts a disposable PostgreSQL ${POSTGRES_VERSION} container"
echo "  2. Runs migration safety tests"
echo "  3. Cleans up the container"
echo ""
echo "Test database: ${TEST_DATABASE_URL}"
echo ""

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠️  Container ${CONTAINER_NAME} already exists. Removing..."
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
fi

# Start PostgreSQL container
echo "🐘 Starting PostgreSQL ${POSTGRES_VERSION} container..."
docker run --name "${CONTAINER_NAME}" \
    -e POSTGRES_USER="${TEST_USER}" \
    -e POSTGRES_PASSWORD="${TEST_PASSWORD}" \
    -e POSTGRES_DB="${TEST_DB}" \
    -p "${TEST_PORT}:5432" \
    -d "postgres:${POSTGRES_VERSION}" \
    > /dev/null

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 3

# Wait for PostgreSQL to accept connections
max_attempts=30
attempt=0
until docker exec "${CONTAINER_NAME}" pg_isready -U "${TEST_USER}" > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ PostgreSQL did not become ready in time"
        docker logs "${CONTAINER_NAME}"
        docker stop "${CONTAINER_NAME}"
        docker rm "${CONTAINER_NAME}"
        exit 1
    fi
    sleep 1
done

echo "✅ PostgreSQL ready"
echo ""

# Run tests
echo "🧪 Running migration safety tests..."
echo ""

cd "$(dirname "$0")/.."
if uv run pytest tests/test_migration_safety.py -v; then
    TEST_RESULT="✅ PASSED"
    EXIT_CODE=0
else
    TEST_RESULT="❌ FAILED"
    EXIT_CODE=1
fi

echo ""
echo "=== Test Result: ${TEST_RESULT} ==="
echo ""

# Cleanup
echo "🧹 Cleaning up..."
docker stop "${CONTAINER_NAME}" > /dev/null
docker rm "${CONTAINER_NAME}" > /dev/null
echo "✅ Container removed"

exit $EXIT_CODE
