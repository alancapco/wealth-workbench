#!/bin/bash

# Stop script for RM Workbench MVP

echo "🛑 Stopping RM Workbench MVP..."
echo ""

# Stop backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || echo "   Backend already stopped"
    rm backend.pid
else
    echo "Stopping any running backend processes..."
    pkill -f "uvicorn app.main:app" 2>/dev/null || echo "   No backend process found"
fi

# Stop frontend
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || echo "   Frontend already stopped"
    rm frontend.pid
else
    echo "Stopping any running frontend processes..."
    pkill -f "next dev" 2>/dev/null || echo "   No frontend process found"
fi

# Stop Docker containers
echo "Stopping PostgreSQL and Redis..."
docker-compose stop postgres redis

echo ""
echo "✅ All services stopped"
echo ""
echo "To completely remove data volumes: docker-compose down -v"
