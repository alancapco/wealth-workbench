#!/bin/bash

# Start script for RM Workbench MVP
# Runs PostgreSQL and Redis in Docker, backend and frontend from code
# Uses uv for Python dependency management

set -e

echo "🚀 Starting RM Workbench MVP..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Run: cp .env.example .env"
    exit 1
fi

echo "✅ .env file found"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Start PostgreSQL and Redis with Docker
echo "🐳 Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

until docker-compose exec -T postgres pg_isready -U rm_user &> /dev/null; do
    echo "   Still waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready"
echo "✅ Redis is running"
echo ""

# Backend setup with uv
cd backend

echo "📦 Installing Python dependencies with uv..."
uv sync

cd ..

echo ""
echo "🎯 Starting Backend (FastAPI)..."
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
cd ..
echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   Logs: tail -f backend.log"

echo ""
echo "🎨 Starting Frontend (Next.js)..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm packages..."
    npm install
fi

npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
cd ..
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "   Logs: tail -f frontend.log"

echo ""
echo "⏳ Waiting for services to initialize (10 seconds)..."
sleep 10

echo ""
echo "🎉 All services started!"
echo ""
echo "📊 Access your application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/docs"
echo ""
echo "📝 View logs:"
echo "   Backend:   tail -f backend.log"
echo "   Frontend:  tail -f frontend.log"
echo "   Postgres:  docker-compose logs -f postgres"
echo "   Redis:     docker-compose logs -f redis"
echo ""
echo "🛑 Stop services: ./stop.sh"
