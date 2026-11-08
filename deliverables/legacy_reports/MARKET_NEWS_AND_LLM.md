# Market Data & News Integration

## Tiger Broker API

All market data and news are sourced from Tiger Broker:

### Market Data
- ✅ Real-time stock quotes
- ✅ Price changes and percentages
- ✅ Volume data
- ✅ Historical data for charting

### Market News
- ✅ **Tiger Broker News Feed** - Primary news source
- ✅ Stock-specific news
- ✅ General market news
- ✅ News timestamps and sources

### Usage

```python
from app.services.market.market_service import market_data_service

# Get real-time quotes
quotes = await market_data_service.get_real_time_quote(["HSBC", "00700.HK"])

# Get market news (Tiger Broker feed)
news = await market_data_service.get_market_news(limit=20)

# Get news for specific symbols
symbol_news = await market_data_service.get_market_news(symbols=["HSBC"], limit=10)

# Detect market signals
signal = await market_data_service.detect_market_signal("HSBC", threshold=2.0)
```

### API Endpoints

```bash
# Get market news from Tiger Broker
GET /api/v1/market/news

# Get news for specific symbols
GET /api/v1/market/news?symbols=HSBC,00700.HK&limit=10

# Get quotes
GET /api/v1/market/quotes?symbols=HSBC,00700.HK

# Detect signals
GET /api/v1/market/signals?symbols=HSBC&threshold=2.0
```

All news displayed on the dashboard comes from Tiger Broker's news feed.

## LLM Integration (OpenAI-Compatible)

All AI/LLM calls use OpenAI-compatible API format:

### Configuration

```bash
# .env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4-turbo-preview
```

### Supported Providers

1. **OpenAI**
   ```bash
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-4-turbo-preview
   ```

2. **Anthropic** (via compatible proxy)
   ```bash
   LLM_BASE_URL=https://api.anthropic.com/v1
   LLM_MODEL=claude-3-opus-20240229
   ```

3. **Local Models** (Ollama, LocalAI, etc.)
   ```bash
   LLM_BASE_URL=http://localhost:8080/v1
   LLM_MODEL=llama2
   ```

### Usage

All copilot services automatically use the configured LLM:

```python
from app.services.copilot.copilot_service import copilot_service

# Generate client brief
brief = await copilot_service.generate_brief(
    client_data, portfolio_data, market_signals, interaction_history
)

# Extract meeting insights
insights = await copilot_service.extract_meeting_insights(
    transcript, client_context
)
```

The service automatically uses:
- `settings.LLM_API_KEY` for authentication
- `settings.LLM_BASE_URL` for the API endpoint
- `settings.LLM_MODEL` for the model name

This allows you to switch between different LLM providers without changing any code!
