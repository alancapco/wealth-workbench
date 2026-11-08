# RM Workbench MVP - Full Stack Implementation

> Next-generation Relationship Manager Workbench with AI-powered copilot orchestration

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL with TimescaleDB + pgvector
- **Market Data**: Tiger Broker OpenAPI SDK
- **CRM**: HubSpot API Integration
- **AI**: OpenAI/Anthropic for copilot orchestration
- **Shariah Tools**: Local integration from `/Volumes/Orico/code/capco/islamic-ai/shariah`

### Frontend
- **Framework**: Next.js 14 (App Router + React 18)
- **Charts**: ECharts + TradingView Lightweight Charts
- **Styling**: Tailwind CSS (Capco design system)
- **State**: SWR for data fetching

## 📋 Prerequisites

1. **Docker & Docker Compose** (recommended for development)
2. **Node.js 20+** and **Python 3.11+** (for local development)
3. **API Keys** - You'll need to register/configure:
   - Tiger Broker API (https://www.itiger.com/openapi/info)
   - HubSpot (you already have this)
   - OpenAI or Anthropic API key

## 🚀 Quick Start

### 1. Clone and Setup Environment

```bash
cd /Users/alanyoung/Orico/code/capco/wealth-workbench

# Copy environment template
cp .env.example .env

# Edit .env and fill in your API keys
nano .env
```

### 2. Start with Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### 3. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed demo data
docker-compose exec backend python -m app.scripts.seed_demo_data
```

## 🔧 Development Setup (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL with extensions
# Make sure you have PostgreSQL with TimescaleDB and pgvector installed

# Run migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
```

## 📝 Environment Variables

Create a `.env` file in the root directory with the following:

```bash
# Database
DATABASE_URL=postgresql://rm_user:your_password@localhost:5432/rm_workbench
POSTGRES_USER=rm_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=rm_workbench

# Tiger Broker API
# Register at: https://www.itiger.com/openapi/info
TIGER_CLIENT_ID=your_tiger_client_id
TIGER_PRIVATE_KEY=/path/to/your/tiger_private_key.pem
TIGER_ACCOUNT=your_tiger_account_number

# HubSpot (you already have this)
HUBSPOT_API_KEY=your_hubspot_api_key
HUBSPOT_ACCESS_TOKEN=your_hubspot_access_token

# AI Services - OpenAI Compatible
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4-turbo-preview

# Market News (optional - Tiger Broker provides news)
MARKET_NEWS_API_KEY=your_news_api_key

# Application
SECRET_KEY=$(openssl rand -hex 32)
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
ENVIRONMENT=development

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Shariah Tools
SHARIAH_TOOLS_PATH=/Volumes/Orico/code/capco/islamic-ai/shariah

# Redis
REDIS_URL=redis://localhost:6379
```

## 🎯 What You Need to Register

### 1. Tiger Broker API ✅ Required
**Why**: Real-time market data, quotes, historical data, market news
**Sign up**: https://www.itiger.com/openapi/info
**What you get**: 
- Client ID
- Private Key (RSA key pair)
- Account number

### 2. HubSpot ✅ Already Have
**Why**: CRM integration, client data sync
**You already have this configured**

### 3. OpenAI-Compatible LLM API ✅ Required
**Why**: AI-powered brief generation, meeting insight extraction
**Options**:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/ (via compatible proxy)
- Any OpenAI-compatible endpoint

## 📊 Features Implemented

### Core Workflow
- ✅ **Client Ranking Algorithm** - Opportunity, Risk, Retention scoring
- ✅ **Market Data Integration** - Tiger Broker real-time quotes and news
- ✅ **Brief Generation** - AI-powered 5-section client briefs
- ✅ **Three Approval Gates** - Gate 1 (Brief), Gate 2 (Consent), Gate 3 (Review)
- ✅ **Provenance Tracking** - Evidence chips on every AI statement
- ✅ **Shariah Compliance** - Screening, zakat calculation, reporting

### Dashboard (My Day)
- ✅ KPI Cards with real-time data
- ✅ ECharts allocation donut chart
- ✅ Performance trend line chart
- ✅ Today's schedule with context
- ✅ Live market news with indicators
- ✅ Priority actions

### Integrations
- ✅ Tiger Broker SDK for market data
- ✅ HubSpot CRM sync
- ✅ Shariah tools integration
- ✅ OpenAI/Anthropic copilot

## 🔌 API Endpoints

### Dashboard
- `GET /api/v1/dashboard/my-day` - Complete dashboard data
- `GET /api/v1/dashboard/kpis` - KPI metrics
- `GET /api/v1/dashboard/allocation` - Portfolio allocation
- `GET /api/v1/dashboard/performance-trend` - Performance data

### Market Data
- `GET /api/v1/market/quotes?symbols=HSBC,00700.HK` - Real-time quotes
- `GET /api/v1/market/news` - Market news
- `GET /api/v1/market/signals` - Detect significant movements
- `GET /api/v1/market/historical/{symbol}` - Historical data

### Clients
- `GET /api/v1/clients` - List all clients
- `GET /api/v1/clients/{id}` - Get client details
- `GET /api/v1/clients/{id}/portfolio` - Client portfolio
- `GET /api/v1/clients/{id}/shariah-report` - Shariah compliance report

### Briefs & Workflow
- `POST /api/v1/briefs/generate` - Generate client brief (Gate 1)
- `POST /api/v1/briefs/approve` - Approve brief
- `POST /api/v1/workflow/consent` - Record consent (Gate 2)
- `POST /api/v1/workflow/review/approve` - Approve review (Gate 3)

## 📚 Documentation

- **API Docs**: http://localhost:8000/api/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/api/redoc
- **Implementation Plan**: `IMPLEMENTATION_PLAN.md`
- **Design Specs**: See `01_Requirements_Specification.md`, `02_Product_Design_Specification.md`

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🔍 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
```

### Tiger Broker API Issues
- Verify your credentials in `.env`
- Check if you're in sandbox mode (set in config)
- Ensure private key path is correct and accessible

### Frontend Can't Connect to Backend
- Check `NEXT_PUBLIC_API_URL` in `.env`
- Verify backend is running on port 8000
- Check CORS settings in backend config

## 🚧 Next Steps

1. **Fill in `.env` file** with your API keys
2. **Start services**: `docker-compose up -d`
3. **Access dashboard**: http://localhost:3000
4. **Explore API docs**: http://localhost:8000/api/docs
5. **Seed demo data** for testing

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review API documentation
3. Verify environment variables
4. Check that all required services are running

## 🏗️ Project Structure

```
wealth-workbench/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API routes
│   │   ├── core/              # Config, database
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Business logic
│   │   │   ├── market/        # Tiger Broker integration
│   │   │   ├── copilot/       # AI orchestration
│   │   │   ├── shariah/       # Shariah tools
│   │   │   ├── crm/           # HubSpot integration
│   │   │   └── ranking/       # Client ranking
│   │   └── main.py            # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js frontend
│   ├── app/                   # App router pages
│   ├── components/            # React components
│   ├── lib/                   # Utilities & API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## ✨ Key Features Aligned with Specifications

All features implemented according to the design specifications in:
- `01_Requirements_Specification.md` - 34 functional requirements
- `02_Product_Design_Specification.md` - UI/UX specifications
- Provenance-first design with evidence chips
- Three human approval gates
- Honest degradation patterns
- Capco black & white professional aesthetic
