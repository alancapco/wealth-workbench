# RM Workbench MVP - Registration & API Keys Guide

## What You Need to Register

### 1. Tiger Broker API ✅ REQUIRED

**Purpose**: Real-time market data, stock quotes, historical prices, market news

**Registration Steps**:
1. Visit: https://www.itiger.com/openapi/info
2. Sign up for a Tiger Broker account
3. Apply for API access (may take 1-2 business days)
4. Generate your API credentials:
   - Client ID
   - Private Key (RSA key pair - download and save securely)
   - Account number

**What you'll get**:
```bash
TIGER_CLIENT_ID=your_client_id_here
TIGER_PRIVATE_KEY=/path/to/private_key.pem
TIGER_ACCOUNT=your_account_number
```

**Pricing**: Free tier available for development, paid plans for production

**Documentation**: https://quant.itiger.com/openapi/py-docs/en/docs/intro/quickStart.html

---

### 2. HubSpot API ✅ ALREADY HAVE

**Purpose**: CRM integration, client data synchronization

**You mentioned you already have HubSpot configured**, but if you need to get access tokens:

1. Visit: https://app.hubspot.com/
2. Go to Settings → Integrations → Private Apps
3. Create a new private app
4. Grant required scopes:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.schemas.contacts.read`

**What you'll get**:
```bash
HUBSPOT_ACCESS_TOKEN=pat-na1-your-access-token
```

---

### 3. LLM API (OpenAI-Compatible) ✅ REQUIRED

**Purpose**: AI-powered copilot for brief generation, meeting insight extraction

**The application uses OpenAI-compatible API calls**, which means you can use:

#### Option A: OpenAI (Recommended)

1. Visit: https://platform.openai.com/
2. Sign up/Login
3. Go to API Keys section
4. Create new secret key
5. Copy and save immediately (shown only once)

**What you'll configure**:
```bash
LLM_API_KEY=sk-proj-your-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4-turbo-preview
```

**Pricing**: Pay-as-you-go, ~$0.03 per 1K tokens for GPT-4

#### Option B: Anthropic Claude (via OpenAI-compatible endpoint)

1. Visit: https://console.anthropic.com/
2. Sign up/Login
3. Go to API Keys
4. Create new key

**What you'll configure**:
```bash
LLM_API_KEY=sk-ant-your-key-here
LLM_BASE_URL=https://api.anthropic.com/v1
LLM_MODEL=claude-3-opus-20240229
```

**Note**: You may need an OpenAI-compatible proxy for Anthropic

#### Option C: Local/Other OpenAI-Compatible Models

Any service with OpenAI-compatible API (Ollama, LocalAI, etc.):

```bash
LLM_API_KEY=your-key-or-blank
LLM_BASE_URL=http://localhost:8080/v1
LLM_MODEL=your-model-name
```

---

### 4. Market News API (OPTIONAL)

**Purpose**: Additional market news sources (Tiger Broker already provides news)

**Options**:
- **NewsAPI**: https://newsapi.org/ (Free tier: 100 requests/day)
- **Alpha Vantage**: https://www.alphavantage.co/ (Free tier available)
- **Finnhub**: https://finnhub.io/ (Free tier: 60 API calls/minute)

Not strictly required as Tiger Broker provides news feed.

---

## Quick Setup Checklist

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and fill in:
# ✅ TIGER_CLIENT_ID=...
# ✅ TIGER_PRIVATE_KEY=...
# ✅ TIGER_ACCOUNT=...
# ✅ HUBSPOT_ACCESS_TOKEN=... (you already have this)
# ✅ LLM_API_KEY=... (OpenAI or compatible)
# ✅ LLM_BASE_URL=... (API endpoint)
# ✅ LLM_MODEL=... (model name)
# ✅ Generate SECRET_KEY with: openssl rand -hex 32

# 3. Shariah tools path (already exists)
# SHARIAH_TOOLS_PATH=/Volumes/Orico/code/capco/islamic-ai/shariah

# 4. Start services
docker-compose up -d

# 5. Seed demo data
docker-compose exec backend python -m app.scripts.seed_demo_data
```

---

## Cost Estimates (Development)

| Service | Free Tier | Expected Monthly Cost (Dev) |
|---------|-----------|----------------------------|
| Tiger Broker API | Limited free tier | $0-50 |
| HubSpot | Free (you have it) | $0 |
| OpenAI API | $5 credit | $10-30 (light usage) |
| PostgreSQL (Docker) | Free | $0 |
| Redis (Docker) | Free | $0 |
| **Total** | | **$10-80/month** |

---

## Security Best Practices

1. **Never commit `.env` to git** - it's in `.gitignore`
2. **Rotate API keys** regularly
3. **Use private key encryption** for Tiger Broker key
4. **Restrict API key permissions** to minimum required scopes
5. **Monitor API usage** to prevent unexpected charges

---

## Troubleshooting

### Tiger Broker Connection Issues
- Verify you're using correct environment (sandbox vs production)
- Check private key path is absolute and file is readable
- Ensure account number matches your application

### OpenAI Rate Limits
- Free tier: 3 requests/minute
- Paid tier: 3,500 requests/minute
- Upgrade to paid if hitting limits

### HubSpot Authentication
- Access tokens expire - check validity
- Verify required scopes are granted
- Test with HubSpot API console first

---

## Ready to Go?

Once you have all API keys configured in `.env`:

```bash
./setup.sh
```

Then visit:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/api/docs
