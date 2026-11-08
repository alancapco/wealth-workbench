# RM Workbench MVP - Quick Start Guide

## 🚀 Quick Start (5 Steps)

### 1. Clone & Navigate
```bash
cd /Users/alanyoung/Orico/code/capco/wealth-workbench
```

### 2. Copy Environment Template
```bash
cp .env.example .env
```

### 3. Fill in API Keys in `.env`

**Required keys** (see `REGISTRATION_GUIDE.md` for registration instructions):

```bash
# Tiger Broker (register at https://www.itiger.com/openapi/info)
TIGER_CLIENT_ID=your_client_id_here
TIGER_PRIVATE_KEY=/absolute/path/to/tiger_private_key.pem
TIGER_ACCOUNT=your_account_number

# HubSpot (you already have this)
HUBSPOT_ACCESS_TOKEN=your_hubspot_token

# OpenAI OR Anthropic (choose one)
OPENAI_API_KEY=sk-your-openai-key
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Database password
POSTGRES_PASSWORD=your_secure_password_here

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)
```

### 4. Start Everything
```bash
./start.sh
```

This will:
- ✅ Check your API keys are configured
- ✅ Start PostgreSQL with TimescaleDB + pgvector
- ✅ Start Redis
- ✅ Start FastAPI backend
- ✅ Create database tables automatically
- ✅ Seed demo data (3 clients with portfolios)
- ✅ Start Next.js frontend

### 5. Open Your Browser

- 🌐 **Dashboard**: http://localhost:3000
- 📚 **API Docs**: http://localhost:8000/api/docs
- 🔍 **Health Check**: http://localhost:8000/health

## 📊 What You'll See

The dashboard will display:
- **4 KPI Cards**: Total AUM, Today's Meetings, Open Actions, Performance
- **Allocation Chart**: ECharts donut showing Equities/Fixed Income/Cash
- **Performance Trend**: Line chart comparing Portfolio vs Benchmark
- **Today's Schedule**: 3 meetings with Kenneth Wong highlighted
- **Market News**: Live feed with pulsing indicators
- **Priority Actions**: 4 color-coded action items
- **Book Stats**: Client count, family offices, avg AUM, etc.

## 🗄️ Demo Data Included

**3 Sample Clients**:
1. **Kenneth Wong** - HKD 45.2M AUM, Private Wealth
   - Holdings in HSBC, Tencent, AIA
   - Recent interactions about rebalancing
2. **Ahmad Rahman** - SGD 32.8M AUM, Shariah-compliant
   - Annual zakat calculation ready
3. **Tan Family Office** - SGD 120.5M AUM, 7 entities
   - Multi-generational structure

## 🔧 Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Rebuild if you change code
docker-compose up -d --build

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U rm_user -d rm_workbench
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing API keys in .env
# - Wrong DATABASE_URL format
# - Shariah tools path doesn't exist (set to /tmp if not available)
```

### Frontend can't connect to backend
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check NEXT_PUBLIC_API_URL in .env
# Should be: NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database connection failed
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart database
docker-compose restart postgres
```

### Demo data not loading
```bash
# Manually run seed script
docker-compose exec backend python -m app.scripts.seed_demo_data
```

## 📖 Next Steps

1. **Explore API**: http://localhost:8000/api/docs
2. **Test endpoints**: Try `/api/v1/dashboard/my-day`
3. **View database**: `docker-compose exec postgres psql -U rm_user -d rm_workbench`
4. **Check logs**: `docker-compose logs -f`

## 🎯 Implementation Status

✅ **Complete**:
- FastAPI backend with all services
- Next.js dashboard with ECharts
- PostgreSQL with TimescaleDB + pgvector
- Tiger Broker market data integration
- HubSpot CRM integration
- OpenAI/Anthropic copilot
- Shariah tools integration
- Docker Compose setup
- Auto-initialization and demo data seeding
- Complete REST API

🔜 **Not Yet Implemented** (requires your API keys):
- Real Tiger Broker market data (needs your credentials)
- Live HubSpot CRM sync (needs your token)
- Real AI brief generation (needs OpenAI/Anthropic key)

Once you configure your API keys, all integrations will work with real data!
