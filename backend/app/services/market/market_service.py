"""
Market Data Service

Quotes and history: Alpha Vantage (GLOBAL_QUOTE / TIME_SERIES_DAILY).
English news: Newsfilter v2, then Yahoo Finance RSS (per NEWS_PROVIDER).
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import asyncio
import os
import re
import time
import xml.etree.ElementTree as ET
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

NEWS_CACHE_SECONDS = 300  # 5-minute cache for news
NEWSFILTER_URL = "https://api.newsfilter.io/search"
NEWSFILTER_COOLDOWN_SECONDS = 60
YAHOO_NEWS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"
YAHOO_USER_AGENT = "Mozilla/5.0 (compatible; WMWorkbench/1.0)"

# Newsfilter indexes US listings. These Hong Kong codes are the US symbols
# for the same issuers.
NEWSFILTER_SYMBOLS = {
    "0005.HK": "HSBC",
    "0700.HK": "TCEHY",
    "00700.HK": "TCEHY",
    "700.HK": "TCEHY",
    "9988.HK": "BABA",
    "09988.HK": "BABA",
}

HK_SNAPSHOT_SYMBOLS = ["HSBC", "TCEHY", "0005.HK", "1299.HK", "0388.HK"]


class MarketDataService:
    def __init__(self):
        self.mode = "LIVE"
        self._av_cache: dict[tuple, tuple[float, dict]] = {}
        self._av_last_request = 0.0
        self._news_cache: dict[tuple, tuple[float, list, str]] = {}
        self._newsfilter_down_until = 0.0
        logger.info(
            "Market service ready (quotes=%s, news=%s)",
            "AlphaVantage" if self.quotes_configured else "unconfigured",
            self._news_provider(),
        )

    @property
    def news_configured(self) -> bool:
        return settings.market_news_configured

    @property
    def quotes_configured(self) -> bool:
        return bool((settings.ALPHAVANTAGE_API_KEY or "").strip())

    def _news_provider(self) -> str:
        return settings.news_provider

    @staticmethod
    def _normalize_lang(lang: Optional[str]) -> str:
        """English-only news pipeline. Any language hint is coerced to en_US."""
        return "en_US"

    def _yahoo_symbol(self, symbol: str) -> str:
        """Yahoo RSS uses 4-digit Hong Kong codes. 00700.HK returns an empty feed."""
        cleaned = symbol.strip().upper()
        if not cleaned.endswith(".HK"):
            return cleaned
        code = cleaned[:-3]
        if not code.isdigit():
            return cleaned
        digits = code.lstrip("0") or "0"
        if len(digits) < 4:
            digits = digits.zfill(4)
        return f"{digits}.HK"

    def _newsfilter_symbol(self, symbol: str) -> Optional[str]:
        cleaned = symbol.strip().upper()
        yahoo = self._yahoo_symbol(cleaned)
        mapped = (
            NEWSFILTER_SYMBOLS.get(cleaned)
            or NEWSFILTER_SYMBOLS.get(yahoo)
            or ALPHAVANTAGE_SYMBOLS.get(cleaned)
            or ALPHAVANTAGE_SYMBOLS.get(yahoo)
        )
        if mapped:
            return mapped
        if "." not in cleaned and cleaned.isalpha():
            return cleaned
        return None

    def _newsfilter_query(self, symbols: Optional[List[str]]) -> Optional[str]:
        if not symbols:
            return "*"
        mapped: List[str] = []
        for symbol in symbols:
            newsfilter_symbol = self._newsfilter_symbol(symbol)
            if newsfilter_symbol and newsfilter_symbol not in mapped:
                mapped.append(newsfilter_symbol)
        if not mapped:
            return None
        if len(mapped) == 1:
            return f"symbols:{mapped[0]}"
        return "(" + " OR ".join(f"symbols:{symbol}" for symbol in mapped) + ")"

    @staticmethod
    def _strip_html(value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value or "")
        return re.sub(r"\s+", " ", text).strip()

    def _parse_iso_timestamp(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()

    def _serialize_article(
        self,
        *,
        article_id: Optional[str],
        title: str,
        content: str,
        timestamp: Optional[str],
        source: str,
        url: Optional[str],
        symbol: Optional[str] = None,
        symbols: Optional[List[str]] = None,
    ) -> Dict:
        item = {
            "id": article_id or url or title,
            "title": title,
            "content": content,
            "timestamp": timestamp,
            "source": source,
            "url": url,
            "symbol": symbol,
        }
        if symbols:
            item["symbols"] = symbols
        return item

    def _fetch_newsfilter_news(self, symbols: Optional[List[str]], limit: int) -> Optional[List[Dict]]:
        if self._news_provider() == "yahoo":
            return None
        key = (settings.NEWSFILTER_API_KEY or "").strip()
        if not key:
            return None
        if time.monotonic() < self._newsfilter_down_until:
            logger.info("Newsfilter circuit open; skipping until cooldown ends")
            return None
        query = self._newsfilter_query(symbols)
        if query is None:
            return None
        try:
            response = requests.post(
                NEWSFILTER_URL,
                headers={"Authorization": key, "Content-Type": "application/json"},
                json={
                    "query": query,
                    "from": 0,
                    "size": max(1, min(limit, 50)),
                    "sort": {"publishedAt": {"order": "desc"}},
                },
                timeout=8,
            )
        except requests.RequestException as exc:
            logger.warning("Newsfilter request failed: %s", exc)
            self._newsfilter_down_until = time.monotonic() + NEWSFILTER_COOLDOWN_SECONDS
            return None
        if response.status_code >= 500:
            logger.warning("Newsfilter HTTP %s", response.status_code)
            self._newsfilter_down_until = time.monotonic() + NEWSFILTER_COOLDOWN_SECONDS
            return None
        if response.status_code >= 400:
            logger.warning("Newsfilter HTTP %s", response.status_code)
            return None
        try:
            payload = response.json()
        except ValueError:
            logger.warning("Newsfilter returned a non-JSON body")
            return None
        articles = payload.get("articles") if isinstance(payload, dict) else None
        if not isinstance(articles, list) or not articles:
            return None
        items = []
        for article in articles[:limit]:
            if not isinstance(article, dict):
                continue
            publisher = article.get("source") if isinstance(article.get("source"), dict) else {}
            tickers = article.get("symbols") if isinstance(article.get("symbols"), list) else []
            items.append(self._serialize_article(
                article_id=article.get("id"),
                title=article.get("title") or "",
                content=article.get("description") or "",
                timestamp=self._parse_iso_timestamp(article.get("publishedAt")),
                source=publisher.get("name") or "Newsfilter",
                url=article.get("sourceUrl") or article.get("url"),
                symbol=tickers[0] if tickers else None,
                symbols=[str(ticker) for ticker in tickers] or None,
            ))
        return items or None

    def _yahoo_symbols(self, symbols: Optional[List[str]]) -> List[str]:
        if symbols:
            yahoo_symbols: List[str] = []
            for symbol in symbols:
                yahoo = self._yahoo_symbol(symbol)
                if yahoo and yahoo not in yahoo_symbols:
                    yahoo_symbols.append(yahoo)
            return yahoo_symbols
        return [
            symbol.strip()
            for symbol in (settings.YAHOO_NEWS_DEFAULT_SYMBOLS or "").split(",")
            if symbol.strip()
        ]

    def _parse_yahoo_rss(self, xml_text: str, limit: int) -> List[Dict]:
        root = ET.fromstring(xml_text)
        items: List[Dict] = []
        seen: set[str] = set()
        for node in root.findall("./channel/item"):
            title = self._strip_html(node.findtext("title") or "")
            link = (node.findtext("link") or "").strip()
            guid = (node.findtext("guid") or link or title).strip()
            if not title or not guid or guid in seen:
                continue
            seen.add(guid)
            published = None
            pub_date = node.findtext("pubDate")
            if pub_date:
                try:
                    published = parsedate_to_datetime(pub_date).astimezone(timezone.utc).isoformat()
                except (TypeError, ValueError, IndexError):
                    published = None
            description = node.find("description")
            content = self._strip_html("".join(description.itertext()) if description is not None else "")
            items.append(self._serialize_article(
                article_id=guid,
                title=title,
                content=content,
                timestamp=published,
                source="Yahoo Finance",
                url=link or None,
            ))
        items.sort(key=lambda row: row.get("timestamp") or "", reverse=True)
        return items[:limit]

    def _fetch_yahoo_news(self, symbols: Optional[List[str]], limit: int) -> Optional[List[Dict]]:
        if self._news_provider() == "newsfilter":
            return None
        yahoo_symbols = self._yahoo_symbols(symbols)
        if not yahoo_symbols:
            return None
        response = requests.get(
            YAHOO_NEWS_URL,
            params={"s": ",".join(yahoo_symbols), "region": "US", "lang": "en-US"},
            headers={"User-Agent": YAHOO_USER_AGENT},
            timeout=8,
        )
        response.raise_for_status()
        items = self._parse_yahoo_rss(response.text, limit)
        return items or None

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

    async def get_real_time_quote(self, symbols: List[str]) -> List[Dict]:
        """Latest quote via Alpha Vantage GLOBAL_QUOTE. Empty when unconfigured."""
        if not self.quotes_configured:
            logger.info("Alpha Vantage not configured; returning no quotes")
            return []
        try:
            logger.info("Fetching Alpha Vantage quotes for %s", symbols)
            return await asyncio.to_thread(self._fetch_av_quotes, symbols)
        except Exception as e:
            logger.error("Error fetching quotes: %s", e)
            return []

    async def get_market_news(
        self,
        symbols: Optional[List[str]] = None,
        limit: int = 20,
        lang: Optional[str] = None,
    ) -> tuple[List[Dict], str, bool]:
        """English news from Newsfilter, then Yahoo Finance RSS.

        ``lang`` is accepted for API compatibility but always treated as English.
        Returns (news_list, source_label, was_cached).
        """
        if os.environ.get("WM_DISABLE_LIVE_NEWS") == "1":
            return [], "none", False

        language = self._normalize_lang(lang)
        normalized = [symbol.strip() for symbol in (symbols or []) if symbol and symbol.strip()]
        cache_key = (tuple(normalized), int(limit), language)
        now = time.monotonic()
        cached = self._news_cache.get(cache_key)
        if cached and now - cached[0] < NEWS_CACHE_SECONDS:
            return cached[1], cached[2], True

        query_symbols = normalized or None
        try:
            provider = self._news_provider()
            if provider in {"newsfilter", "newsfilter_yahoo"}:
                articles = await asyncio.to_thread(self._fetch_newsfilter_news, query_symbols, limit)
                if articles:
                    self._news_cache[cache_key] = (now, articles, "newsfilter")
                    return articles, "newsfilter", False

            if provider in {"yahoo", "newsfilter_yahoo"}:
                try:
                    yahoo_news = await asyncio.to_thread(self._fetch_yahoo_news, query_symbols, limit)
                except Exception as exc:
                    logger.error("Yahoo Finance news failed: %s", exc)
                    yahoo_news = None
                if yahoo_news:
                    self._news_cache[cache_key] = (now, yahoo_news, "yahoo_finance")
                    return yahoo_news, "yahoo_finance", False

            return [], "none", False
        except Exception as e:
            logger.error("Error fetching news: %s", e)
            return [], "none", False

    async def get_market_quotes_snapshot(self) -> List[Dict]:
        """Fetch a fixed set of HK-relevant tickers and return their quotes."""
        return await self.get_real_time_quote(HK_SNAPSHOT_SYMBOLS)

    async def detect_market_signal(self, symbol: str, threshold: float = 2.0) -> Optional[Dict]:
        """Detect significant market movements from Alpha Vantage quotes."""
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
            logger.error("Error detecting signal for %s: %s", symbol, e)
            return None

    async def get_historical_data(self, symbol: str, period: str = "1d", limit: int = 100) -> List[Dict]:
        """Daily bars from Alpha Vantage TIME_SERIES_DAILY. Empty when unconfigured."""
        if not self.quotes_configured:
            logger.info("Alpha Vantage not configured; returning no history for %s", symbol)
            return []
        try:
            logger.info("Fetching Alpha Vantage daily bars for %s", symbol)
            rows = await asyncio.to_thread(self._fetch_av_history, symbol, limit)
            return rows or []
        except Exception as e:
            logger.error("Error fetching historical data for %s: %s", symbol, e)
            return []

    def set_mode(self, mode: str):
        """Switch between LIVE and REPLAY mode (metadata only; AV is EOD)."""
        if mode in ["LIVE", "REPLAY"]:
            self.mode = mode
            logger.info("Market data mode set to %s", mode)
        else:
            raise ValueError("Mode must be 'LIVE' or 'REPLAY'")


# Singleton instance
market_data_service = MarketDataService()
