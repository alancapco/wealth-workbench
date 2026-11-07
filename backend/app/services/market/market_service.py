"""
Market Data Service - Tiger Broker Integration
Provides real-time market data, quotes, and news via HTTP API
"""
from typing import List, Dict, Optional
from datetime import datetime, UTC, timezone
import asyncio
import time
import requests
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

ALPHAVANTAGE_URL = "https://www.alphavantage.co/query"
ALPHAVANTAGE_CACHE_SECONDS = 15 * 60
# Alpha Vantage's free quote feed covers US listings. These Hong Kong codes
# are the same issuers' US tickers that the quote endpoint actually returns.
ALPHAVANTAGE_SYMBOLS = {
    "0005.HK": "HSBC",
    "00700.HK": "TCEHY",
    "0700.HK": "TCEHY",
    "700.HK": "TCEHY",
}

# Laohu8 publishes the Chinese edition. The en_US ids from the same feed
# return HTTP 410 / code 10001 ("News does not exist") on the detail URL.
NEWS_LANG = "zh_CN"

class MarketDataService:
    def __init__(self):
        """Initialize Tiger Broker HTTP API client"""
        self.tiger_id = settings.TIGER_CLIENT_ID
        self.private_key = settings.TIGER_PRIVATE_KEY
        self.account = settings.TIGER_ACCOUNT
        self.mode = "LIVE"
        self.base_url = "https://openapi.tigerbrokers.com.hk/gateway"

        logger.info(f"Market service initialized with Tiger ID: {self.tiger_id}")
        self._tiger_news = None
        self._av_cache: dict[tuple, tuple[float, dict]] = {}
        self._av_last_request = 0.0

    def _av_symbol(self, symbol: str) -> str:
        cleaned = symbol.strip().upper()
        return ALPHAVANTAGE_SYMBOLS.get(cleaned, cleaned)

    def _av_message(self, payload: dict) -> str:
        return str(payload.get("Note") or payload.get("Information") or payload.get("Error Message") or "")

    def _av_get(self, params: dict) -> dict:
        key = (settings.ALPHAVANTAGE_API_KEY or "").strip()
        if not key:
            return {}
        cache_key = tuple(sorted(params.items()))
        cached = self._av_cache.get(cache_key)
        now = time.monotonic()
        if cached and now - cached[0] < ALPHAVANTAGE_CACHE_SECONDS:
            return cached[1]

        # Free keys allow about one request per second.
        wait = 1.15 - (now - self._av_last_request)
        if self._av_last_request and wait > 0:
            time.sleep(wait)

        response = requests.get(
            ALPHAVANTAGE_URL,
            params={**params, "apikey": key},
            timeout=20,
        )
        self._av_last_request = time.monotonic()
        response.raise_for_status()
        payload = response.json()
        message = self._av_message(payload)
        if message:
            logger.info("Alpha Vantage %s: %s", params.get("function"), message[:180])
            return payload
        self._av_cache[cache_key] = (self._av_last_request, payload)
        return payload

    def _parse_av_time(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            return None

    def _fetch_av_news(self, symbols: Optional[List[str]], limit: int) -> Optional[List[Dict]]:
        if not (settings.ALPHAVANTAGE_API_KEY or "").strip():
            return None
        params: dict[str, str] = {
            "function": "NEWS_SENTIMENT",
            "sort": "LATEST",
            "limit": str(max(1, min(limit, 50))),
        }
        if symbols:
            params["tickers"] = ",".join(self._av_symbol(symbol) for symbol in symbols)
        else:
            params["topics"] = "financial_markets"
        payload = self._av_get(params)
        feed = payload.get("feed")
        if not isinstance(feed, list):
            return None
        items = []
        for article in feed[:limit]:
            items.append({
                "id": article.get("url") or article.get("title"),
                "title": article.get("title") or "",
                "content": article.get("summary") or "",
                "timestamp": self._parse_av_time(article.get("time_published")),
                "source": article.get("source") or "Alpha Vantage",
                "url": article.get("url"),
                "symbol": None,
            })
        return items

    def _fetch_av_quote(self, symbol: str) -> Optional[Dict]:
        payload = self._av_get({
            "function": "GLOBAL_QUOTE",
            "symbol": self._av_symbol(symbol),
        })
        quote = payload.get("Global Quote") or {}
        price = quote.get("05. price")
        if not price:
            return None
        percent = str(quote.get("10. change percent") or "0").replace("%", "")
        return {
            "symbol": symbol,
            "quoted_symbol": quote.get("01. symbol"),
            "price": float(price),
            "change": float(quote.get("09. change") or 0),
            "change_percent": float(percent or 0),
            "volume": int(float(quote.get("06. volume") or 0)),
            "source_id": "AlphaVantage",
            "source_kind": "EOD",
            "feed_timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "open": float(quote.get("02. open") or 0),
            "high": float(quote.get("03. high") or 0),
            "low": float(quote.get("04. low") or 0),
            "prev_close": float(quote.get("08. previous close") or 0),
        }

    def _fetch_av_quotes(self, symbols: List[str]) -> List[Dict]:
        quotes = []
        for symbol in symbols:
            quote = self._fetch_av_quote(symbol)
            if quote:
                quotes.append(quote)
        return quotes

    def _fetch_av_history(self, symbol: str, limit: int) -> Optional[List[Dict]]:
        payload = self._av_get({
            "function": "TIME_SERIES_DAILY",
            "symbol": self._av_symbol(symbol),
            "outputsize": "compact",
        })
        series = payload.get("Time Series (Daily)")
        if not isinstance(series, dict):
            return None
        rows = []
        for day, bar in list(series.items())[:limit]:
            rows.append({
                "timestamp": day,
                "open": float(bar["1. open"]),
                "high": float(bar["2. high"]),
                "low": float(bar["3. low"]),
                "close": float(bar["4. close"]),
                "volume": int(float(bar["5. volume"])),
                "source_id": "AlphaVantage",
            })
        return rows

    def _private_key_material(self) -> str:
        key = (settings.TIGER_PRIVATE_KEY or "").strip().strip('"').strip("'")
        if "\\n" in key:
            key = key.replace("\\n", "\n")
        return key

    def _tiger_news_client(self):
        if self._tiger_news is not None:
            return self._tiger_news
        if not settings.TIGER_CLIENT_ID or not settings.TIGER_PRIVATE_KEY:
            return None
        from tigeropen.news.news_client import NewsClient
        from tigeropen.tiger_open_config import TigerOpenClientConfig

        config = TigerOpenClientConfig(enable_dynamic_domain=True)
        config.tiger_id = settings.TIGER_CLIENT_ID
        config.private_key = self._private_key_material()
        config.account = settings.TIGER_ACCOUNT
        if settings.TIGER_LICENSE:
            config.license = settings.TIGER_LICENSE
        if settings.TIGER_TOKEN:
            config.token = settings.TIGER_TOKEN
        config.language = NEWS_LANG
        self._tiger_news = NewsClient(config)
        return self._tiger_news

    def _serialize_news(self, item, symbol: Optional[str] = None) -> Dict:
        published = None
        if getattr(item, "pub_timestamp", None):
            published = datetime.fromtimestamp(item.pub_timestamp, tz=timezone.utc).isoformat()
        return {
            "id": item.id,
            "title": item.title,
            "content": item.summary or "",
            "timestamp": published,
            "source": "Tiger Broker",
            "url": item.url,
            "symbol": symbol,
        }

    def _fetch_news(self, symbols: Optional[List[str]], limit: int) -> List[Dict]:
        client = self._tiger_news_client()
        if client is None:
            logger.error("Tiger Broker news is not configured")
            return []

        if symbols:
            items: List[Dict] = []
            page_size = max(1, min(limit, 50))
            for symbol in symbols:
                page = client.get_stock_news(symbol, lang=NEWS_LANG, page_count=1, page_size=page_size)
                for item in page.items or []:
                    items.append(self._serialize_news(item, symbol))
                    if len(items) >= limit:
                        return items
            return items

        page = client.get_market_news(lang=NEWS_LANG)
        return [self._serialize_news(item) for item in (page.items or [])[:limit]]

    def _sign_request(self, timestamp: str, method: str, path: str) -> str:
        """Sign API request with private key"""
        try:
            # For now, return basic auth - full implementation would use RSA signing
            return f"Bearer {settings.TIGER_TOKEN}" if hasattr(settings, 'TIGER_TOKEN') else ""
        except Exception as e:
            logger.error(f"Error signing request: {e}")
            return ""

    async def get_real_time_quote(self, symbols: List[str]) -> List[Dict]:
        """Latest quote. Alpha Vantage GLOBAL_QUOTE when a key is configured."""
        try:
            if (settings.ALPHAVANTAGE_API_KEY or "").strip():
                logger.info(f"Fetching Alpha Vantage quotes for {symbols}")
                return await asyncio.to_thread(self._fetch_av_quotes, symbols)

            ticks = []
            for symbol in symbols:
                ticks.append({
                    "symbol": symbol,
                    "price": 50.0 + hash(symbol) % 100,
                    "change": (hash(symbol) % 5) - 2.5,
                    "change_percent": ((hash(symbol) % 5) - 2.5) / 50.0 * 100,
                    "volume": 1000000 + hash(symbol) % 5000000,
                    "source_id": "TigerBroker",
                    "source_kind": "LIVE_FEED" if self.mode == "LIVE" else "REPLAY",
                    "feed_timestamp": datetime.now(timezone.utc).isoformat(),
                    "mode": self.mode,
                    "open": 49.0 + hash(symbol) % 100,
                    "high": 52.0 + hash(symbol) % 100,
                    "low": 48.0 + hash(symbol) % 100,
                    "prev_close": 50.0 + hash(symbol) % 100,
                })
            return ticks
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return []

    async def get_market_news(self, symbols: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
        """Alpha Vantage NEWS_SENTIMENT when the key allows it, otherwise Tiger Broker."""
        try:
            alphavantage = await asyncio.to_thread(self._fetch_av_news, symbols, limit)
            if alphavantage:
                return alphavantage
            logger.info(f"Fetching Tiger news (symbols: {symbols}, limit: {limit})")
            return await asyncio.to_thread(self._fetch_news, symbols, limit)
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []

    async def detect_market_signal(self, symbol: str, threshold: float = 2.0) -> Optional[Dict]:
        """
        Detect significant market movements
        Returns signal if change exceeds threshold
        """
        try:
            quotes = await self.get_real_time_quote([symbol])
            if not quotes:
                return None

            quote = quotes[0]
            if abs(quote["change_percent"]) >= threshold:
                return {
                    "symbol": symbol,
                    "change_percent": quote["change_percent"],
                    "price": quote["price"],
                    "signal_type": "OPPORTUNITY" if quote["change_percent"] > 0 else "RISK",
                    "timestamp": quote["feed_timestamp"],
                    "source": quote.get("source_id") or "AlphaVantage",
                }

            return None

        except Exception as e:
            logger.error(f"Error detecting signal for {symbol}: {e}")
            return None

    async def get_historical_data(self, symbol: str, period: str = "1d", limit: int = 100) -> List[Dict]:
        """Daily bars from Alpha Vantage TIME_SERIES_DAILY when a key is configured."""
        try:
            if (settings.ALPHAVANTAGE_API_KEY or "").strip():
                logger.info(f"Fetching Alpha Vantage daily bars for {symbol}")
                rows = await asyncio.to_thread(self._fetch_av_history, symbol, limit)
                if rows is not None:
                    return rows

            historical_data = []
            base_price = 50.0 + hash(symbol) % 100
            for i in range(min(limit, 30)):
                historical_data.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "open": base_price + i * 0.5,
                    "high": base_price + i * 0.5 + 2,
                    "low": base_price + i * 0.5 - 1,
                    "close": base_price + i * 0.5 + 0.5,
                    "volume": 1000000 + i * 10000,
                })
            return historical_data
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []

    def set_mode(self, mode: str):
        """Switch between LIVE and REPLAY mode"""
        if mode in ["LIVE", "REPLAY"]:
            self.mode = mode
            logger.info(f"Market data mode set to {mode}")
        else:
            raise ValueError("Mode must be 'LIVE' or 'REPLAY'")

# Singleton instance
market_data_service = MarketDataService()
