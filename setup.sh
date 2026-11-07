#!/bin/bash

# Setup script for RM Workbench MVP
# This script initializes the development environment

set -e

echo "🚀 Setting up RM Workbench MVP..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and fill in your API keys before proceeding!"
    echo "   Required: TIGER_CLIENT_ID, TIGER_PRIVATE_KEY, TIGER_ACCOUNT"
    echo "   Required: HUBSPOT_ACCESS_TOKEN"
    echo "   Required: OPENAI_API_KEY or ANTHROPIC_API_KEY"
    exit 1
fi

echo "✅ .env file found"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/app/{api/v1/endpoints,core,models,schemas,services/{market,copilot,shariah,crm,ranking},db}
mkdir -p frontend/{app,components,lib,public}

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check if database is ready
until docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER:-rm_user} &> /dev/null; do
    echo "   Waiting for database..."
    sleep 2
done

echo "✅ PostgreSQL is ready"

# Wait a bit more for backend to initialize
echo "⏳ Waiting for backend to initialize (this includes table creation and demo data seeding)..."
sleep 15

# Check if backend is responding
echo "🔍 Checking backend health..."
until curl -f http://localhost:8000/health &> /dev/null; do
    echo "   Waiting for backend API..."
    sleep 3
done

echo "✅ Backend is responding!"
echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Services running:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/api/docs"
echo ""
echo "🔍 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
echo ""
echo "⚠️  Remember to fill in your API keys in .env file!"
