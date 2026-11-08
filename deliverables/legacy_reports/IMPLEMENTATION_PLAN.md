# RM Workbench MVP - Full Implementation Plan

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with extensions:
  - TimescaleDB (time-series market data)
  - pgvector (semantic search for client memory)
- **Market Data**: Tiger Broker OpenAPI SDK
- **CRM Integration**: HubSpot API
- **Shariah Tools**: Local integration from `/Volumes/Orico/code/capco/islamic-ai/shariah`

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Charts**: ECharts + TradingView Lightweight Charts
- **UI**: Capco design system (black & white, professional)

### APIs & Integrations Needed
1. **Tiger Broker** - Market data, news, real-time quotes
2. **HubSpot** (already registered) - CRM integration
3. **OpenAI/Anthropic** - LLM for copilot (will use .env)
4. Market news feed integration

## Project Structure

```
wealth-workbench/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   │   ├── market/     # Market data service (Tiger Broker)
│   │   │   ├── copilot/    # AI orchestration
│   │   │   ├── shariah/    # Shariah tools integration
│   │   │   ├── crm/        # HubSpot integration
│   │   │   └── ranking/    # Client ranking logic
│   │   └── db/             # Database utilities
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # Next.js application
│   ├── app/               # App router
│   ├── components/        # React components
│   ├── lib/              # Utilities
│   ├── public/           # Static assets
│   └── package.json
├── docker-compose.yml     # Development environment
└── .env.example          # Environment variables template
```

## Environment Variables Required (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/rm_workbench
POSTGRES_USER=rm_user
POSTGRES_PASSWORD=
POSTGRES_DB=rm_workbench

# Tiger Broker API
TIGER_CLIENT_ID=
TIGER_PRIVATE_KEY=
TIGER_ACCOUNT=

# HubSpot
HUBSPOT_API_KEY=
HUBSPOT_ACCESS_TOKEN=

# OpenAI/Anthropic
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Market News (if separate)
MARKET_NEWS_API_KEY=

# Application
SECRET_KEY=
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Implementation Phases

### Phase 1: Infrastructure Setup
1. PostgreSQL with TimescaleDB + pgvector
2. FastAPI backend structure
3. Next.js frontend structure
4. Docker development environment

### Phase 2: Core Backend Services
1. Market data service (Tiger Broker integration)
2. Database models and migrations
3. Client memory (D5) service
4. Copilot orchestration core

### Phase 3: Frontend Dashboard
1. My Day dashboard with ECharts
2. TradingView charts for portfolio
3. Client cards with context
4. Live market data display

### Phase 4: Workflow Implementation
1. Client ranking algorithm
2. Brief generation
3. Meeting review workflow
4. Three approval gates

### Phase 5: Integrations
1. HubSpot CRM sync
2. Shariah tools integration
3. Market news feed
4. Demo data generator

## Next Steps
1. Create backend structure with FastAPI
2. Set up Next.js frontend
3. Configure PostgreSQL with extensions
4. Implement market data service
