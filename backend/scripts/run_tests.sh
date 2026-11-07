#!/bin/bash
set -e

echo "Starting PostgreSQL test container..."
docker-compose -f docker-compose.test.yml up -d

echo "Waiting for PostgreSQL to be ready..."
sleep 5

echo "Running tests..."
uv run pytest --tb=short -v

echo "Stopping PostgreSQL container..."
docker-compose -f docker-compose.test.yml down
