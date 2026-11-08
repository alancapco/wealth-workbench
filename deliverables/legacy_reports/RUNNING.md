# RM Workbench MVP - Quick Start

## 🚀 Running the Application

### Start Everything
```bash
./start.sh
```

This will:
1. ✅ Start PostgreSQL and Redis in Docker containers
2. ✅ Create Python virtual environment and install dependencies
3. ✅ Create database tables automatically
4. ✅ Seed demo data (3 clients with portfolios)
5. ✅ Start FastAPI backend on port 8000
6. ✅ Install npm packages and start Next.js frontend on port 3000

### Stop Everything
```bash
./stop.sh
```

This will:
- Stop backend and frontend processes
- Stop PostgreSQL and Redis containers
- Keep data volumes intact

### Clean Restart (Remove All Data)
```bash
./stop.sh
docker-compose down -v  # Remove data volumes
./start.sh
```

## 📊 Access Points

Once started:
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

## 📝 View Logs

```bash
# Backend logs
tail -f backend.log

# Frontend logs  
tail -f frontend.log

# PostgreSQL logs
docker-compose logs -f postgres

# Redis logs
docker-compose logs -f redis

# All Docker logs
docker-compose logs -f
```

## 🔧 Manual Setup (First Time)

### Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

## 🗄️ Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U rm_user -d rm_workbench

# View tables
\dt

# Query clients
SELECT id, name, aum, currency FROM clients;

# Exit
\q
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Database Issues
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Reset database completely
docker-compose down -v
./start.sh
```

### Python Dependencies
```bash
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Node Dependencies
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## ✨ What's Running

- **PostgreSQL** (Docker): Port 5432
  - User: rm_user
  - Database: rm_workbench
  - Extensions: TimescaleDB, pgvector

- **Redis** (Docker): Port 6379
  - Used for caching

- **FastAPI Backend**: Port 8000
  - Auto-reload enabled for development
  - All API endpoints available
  - Demo data loaded

- **Next.js Frontend**: Port 3000
  - Auto-reload enabled
  - Connected to backend
  - Dashboard ready to use

## 🎯 Demo Data

The application comes with 3 pre-loaded clients:

1. **Kenneth Wong** - HKD 45.2M
   - 3 stock holdings
   - Recent interactions about rebalancing
   
2. **Ahmad Rahman** - SGD 32.8M
   - Shariah-compliant client
   
3. **Tan Family Office** - SGD 120.5M
   - 7 entities configured

All visible in the dashboard at http://localhost:3000
