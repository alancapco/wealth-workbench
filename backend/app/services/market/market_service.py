"""
Market Data Service - Tiger Broker Integration
Provides real-time market data, quotes, and news via HTTP API
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone
import asyncio
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

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
        """
        Get real-time quotes for given symbols
        Returns mock data for now since Tiger SDK has dependency issues
        """
        try:
            logger.info(f"Fetching quotes for {symbols}")

            # Mock data for demo - replace with actual API calls when Tiger SDK is working
            ticks = []
            for symbol in symbols:
                tick_data = {
                    "symbol": symbol,
                    "price": 50.0 + hash(symbol) % 100,
                    "change": (hash(symbol) % 5) - 2.5,
                    "change_percent": ((hash(symbol) % 5) - 2.5) / 50.0 * 100,
                    "volume": 1000000 + hash(symbol) % 5000000,
                    "source_id": "TigerBroker",
                    "source_kind": "LIVE_FEED" if self.mode == "LIVE" else "REPLAY",
                    "feed_timestamp": datetime.now(),
                    "mode": self.mode,
                    "open": 49.0 + hash(symbol) % 100,
                    "high": 52.0 + hash(symbol) % 100,
                    "low": 48.0 + hash(symbol) % 100,
                    "prev_close": 50.0 + hash(symbol) % 100,
                }
                ticks.append(tick_data)

            logger.info(f"Retrieved {len(ticks)} quotes")
            return ticks

        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return []

    async def get_market_news(self, symbols: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
        """Market highlights, or per-symbol news when symbols are supplied. Source: Tiger Broker."""
        try:
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
                    "source": "TigerBroker",
                }

            return None

        except Exception as e:
            logger.error(f"Error detecting signal for {symbol}: {e}")
            return None

    async def get_historical_data(self, symbol: str, period: str = "1d", limit: int = 100) -> List[Dict]:
        """
        Get historical price data for charting
        Returns mock data for demo
        """
        try:
            logger.info(f"Fetching historical data for {symbol}")

            # Mock historical data
            historical_data = []
            base_price = 50.0 + hash(symbol) % 100

            for i in range(min(limit, 30)):
                data_point = {
                    "timestamp": datetime.now(),
                    "open": base_price + i * 0.5,
                    "high": base_price + i * 0.5 + 2,
                    "low": base_price + i * 0.5 - 1,
                    "close": base_price + i * 0.5 + 0.5,
                    "volume": 1000000 + i * 10000,
                }
                historical_data.append(data_point)

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
