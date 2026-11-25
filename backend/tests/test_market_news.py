"""English market news: Newsfilter v2, Yahoo Finance RSS fallback, and dashboard unpacking."""
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.services.market.market_service import MarketDataService

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<item>
<title>First headline</title>
<link>https://finance.yahoo.com/a</link>
<description>First &amp; body</description>
<guid>guid-1</guid>
<pubDate>Sun, 22 Nov 2026 01:39:28 +0000</pubDate>
</item>
<item>
<title>Duplicate</title>
<link>https://finance.yahoo.com/a</link>
<description>dup</description>
<guid>guid-1</guid>
<pubDate>Sun, 22 Nov 2026 01:39:28 +0000</pubDate>
</item>
<item>
<title>Older</title>
<link>https://finance.yahoo.com/b</link>
<description><p>Older body</p></description>
<guid>guid-2</guid>
<pubDate>Sat, 21 Nov 2026 01:39:28 +0000</pubDate>
</item>
</channel></rss>
"""

NEWSFILTER_ARTICLE = {
    "articles": [{
        "id": "ee56421c7fa15419833d3f9ccb984e09",
        "title": "Meta Reports Third Quarter 2026 Results",
        "description": "Teaser",
        "sourceUrl": "https://www.prnewswire.com/news-releases/meta.html",
        "url": "https://newsfilter.io/articles/meta",
        "publishedAt": "2026-10-21T16:01:00.000-04:00",
        "source": {"id": "prnewswire", "name": "PR Newswire"},
        "symbols": ["META"],
    }]
}


@pytest.fixture
def service(monkeypatch):
    monkeypatch.delenv("WM_DISABLE_LIVE_NEWS", raising=False)
    monkeypatch.setattr(settings, "NEWSFILTER_API_KEY", "test-newsfilter-key")
    monkeypatch.setattr(settings, "NEWS_PROVIDER", "newsfilter_yahoo")
    monkeypatch.setattr(settings, "YAHOO_NEWS_DEFAULT_SYMBOLS", "^GSPC,AAPL")
    monkeypatch.setattr(settings, "ALPHAVANTAGE_API_KEY", "")
    return MarketDataService()


def _response(status_code=200, payload=None, text=""):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.json.return_value = payload or {}
    response.raise_for_status = MagicMock()
    return response


def test_yahoo_symbol_normalizes_five_digit_hk_codes(service):
    assert service._yahoo_symbol("00700.HK") == "0700.HK"
    assert service._yahoo_symbol("00005.HK") == "0005.HK"
    assert service._yahoo_symbol("0005.HK") == "0005.HK"
    assert service._yahoo_symbol("D05.SI") == "D05.SI"
    assert service._yahoo_symbol("^HSI") == "^HSI"


def test_newsfilter_parses_publisher_and_utc_timestamp(service, monkeypatch):
    post = MagicMock(return_value=_response(payload=NEWSFILTER_ARTICLE))
    monkeypatch.setattr("app.services.market.market_service.requests.post", post)

    items = service._fetch_newsfilter_news(["META"], 5)

    assert items[0]["title"] == "Meta Reports Third Quarter 2026 Results"
    assert items[0]["content"] == "Teaser"
    assert items[0]["source"] == "PR Newswire"
    assert items[0]["url"] == "https://www.prnewswire.com/news-releases/meta.html"
    assert items[0]["symbol"] == "META"
    assert items[0]["timestamp"].startswith("2026-10-21T20:01:00")
    assert post.call_args.kwargs["json"]["query"] == "symbols:META"
    assert post.call_args.kwargs["headers"]["Authorization"] == "test-newsfilter-key"


def test_newsfilter_502_opens_circuit_breaker(service, monkeypatch):
    post = MagicMock(return_value=_response(status_code=502))
    monkeypatch.setattr("app.services.market.market_service.requests.post", post)

    assert service._fetch_newsfilter_news(["AAPL"], 3) is None
    assert service._fetch_newsfilter_news(["AAPL"], 3) is None

    assert post.call_count == 1
    assert service._newsfilter_down_until > time.monotonic()


def test_yahoo_rss_dedupes_sorts_and_strips_html(service):
    items = service._parse_yahoo_rss(RSS, limit=10)

    assert [item["title"] for item in items] == ["First headline", "Older"]
    assert items[0]["content"] == "First & body"
    assert items[1]["content"] == "Older body"
    assert items[0]["source"] == "Yahoo Finance"
    assert items[0]["timestamp"].startswith("2026-11-22T01:39:28")


@pytest.mark.asyncio
async def test_english_news_falls_back_to_yahoo_and_normalizes_hk(service, monkeypatch):
    post = MagicMock(return_value=_response(status_code=502))
    get = MagicMock(return_value=_response(text=RSS))
    monkeypatch.setattr("app.services.market.market_service.requests.post", post)
    monkeypatch.setattr("app.services.market.market_service.requests.get", get)

    news, source, cached = await service.get_market_news(symbols=["00700.HK"], limit=5)

    assert cached is False
    assert source == "yahoo_finance"
    assert news[0]["title"] == "First headline"
    assert post.call_args.kwargs["json"]["query"] == "symbols:TCEHY"
    assert get.call_args.kwargs["params"]["s"] == "0700.HK"
    assert get.call_args.kwargs["params"]["lang"] == "en-US"


@pytest.mark.asyncio
async def test_missing_symbols_use_the_default_yahoo_basket(service, monkeypatch):
    monkeypatch.setattr(settings, "NEWSFILTER_API_KEY", "")
    post = MagicMock(side_effect=AssertionError("Newsfilter called without a key"))
    get = MagicMock(return_value=_response(text=RSS))
    monkeypatch.setattr("app.services.market.market_service.requests.post", post)
    monkeypatch.setattr("app.services.market.market_service.requests.get", get)

    news, source, _ = await service.get_market_news(limit=5)

    assert source == "yahoo_finance"
    assert news
    assert get.call_args.kwargs["params"]["s"] == "^GSPC,AAPL"
    post.assert_not_called()


@pytest.mark.asyncio
async def test_english_newsfilter_success_does_not_call_yahoo(service, monkeypatch):
    post = MagicMock(return_value=_response(payload=NEWSFILTER_ARTICLE))
    get = MagicMock(side_effect=AssertionError("Yahoo called after Newsfilter success"))
    monkeypatch.setattr("app.services.market.market_service.requests.post", post)
    monkeypatch.setattr("app.services.market.market_service.requests.get", get)

    news, source, _ = await service.get_market_news(symbols=["AAPL"], limit=4, lang="en_US")

    assert source == "newsfilter"
    assert news[0]["source"] == "PR Newswire"
    get.assert_not_called()


@pytest.mark.asyncio
async def test_english_path_never_calls_alpha_vantage_news(service, monkeypatch):
    post = MagicMock(return_value=_response(status_code=502))
    get = MagicMock(return_value=_response(text=RSS))
    monkeypatch.setattr("app.services.market.market_service.requests.post", post)
    monkeypatch.setattr("app.services.market.market_service.requests.get", get)
    # Removed from the English pipeline; must stay unused.
    if hasattr(service, "_fetch_av_news"):
        monkeypatch.setattr(service, "_fetch_av_news", MagicMock(side_effect=AssertionError("AV news")))

    news, source, _ = await service.get_market_news(symbols=["AAPL"], limit=3)
    assert source == "yahoo_finance"
    assert news


@pytest.mark.asyncio
async def test_lang_aliases_share_the_same_cache_key(service, monkeypatch):
    get = MagicMock(return_value=_response(text=RSS))
    monkeypatch.setattr(settings, "NEWSFILTER_API_KEY", "")
    monkeypatch.setattr("app.services.market.market_service.requests.get", get)

    first, source, cached = await service.get_market_news(limit=2, lang="en-US")
    second, _, cached_hit = await service.get_market_news(limit=2, lang="en_US")

    assert source == "yahoo_finance"
    assert first == second
    assert cached is False
    assert cached_hit is True
    assert get.call_count == 1


def test_market_news_configured_matches_provider_modes(monkeypatch):
    monkeypatch.setattr(settings, "NEWSFILTER_API_KEY", "")
    monkeypatch.setattr(settings, "NEWS_PROVIDER", "bogus")
    assert settings.news_provider == "newsfilter_yahoo"
    assert settings.market_news_configured is True

    monkeypatch.setattr(settings, "NEWS_PROVIDER", "newsfilter")
    assert settings.market_news_configured is False

    monkeypatch.setattr(settings, "NEWSFILTER_API_KEY", "key")
    assert settings.market_news_configured is True


@pytest.mark.asyncio
async def test_zh_cn_lang_is_coerced_to_english_pipeline(service, monkeypatch):
    """Chinese lang hint is ignored; English Newsfilter/Yahoo path runs."""
    monkeypatch.setattr(settings, "NEWSFILTER_API_KEY", "")
    get = MagicMock(return_value=_response(text=RSS))
    post = MagicMock(side_effect=AssertionError("Newsfilter without key"))
    monkeypatch.setattr("app.services.market.market_service.requests.get", get)
    monkeypatch.setattr("app.services.market.market_service.requests.post", post)

    news, source, _ = await service.get_market_news(lang="zh_CN", limit=3)

    assert source == "yahoo_finance"
    assert news
    assert get.call_args.kwargs["params"]["lang"] == "en-US"


@pytest.mark.asyncio
async def test_disabled_live_news_does_not_call_providers(service, monkeypatch):
    monkeypatch.setenv("WM_DISABLE_LIVE_NEWS", "1")
    post = MagicMock(side_effect=AssertionError("network"))
    monkeypatch.setattr("app.services.market.market_service.requests.post", post)

    news, source, cached = await service.get_market_news(limit=2)

    assert (news, source, cached) == ([], "none", False)
    post.assert_not_called()


@pytest.mark.asyncio
async def test_dashboard_my_day_news_is_a_list_of_articles(monkeypatch):
    from app.api.v1.endpoints import dashboard as dashboard_endpoint
    from app.services.market.market_service import market_data_service

    async def fake_news(*args, **kwargs):
        return ([{"id": "1", "title": "English headline", "content": "Body"}], "yahoo_finance", False)

    async def fake_day(db):
        return {
            "focus": [],
            "pipeline_open": 0,
            "weighted_forecast_usd": 0,
            "rpq_expiring": 0,
            "unread_notifications": 0,
            "recent": [],
        }

    monkeypatch.setattr(market_data_service, "get_market_news", fake_news)
    monkeypatch.setattr("app.services.journey.service.my_day", fake_day)
    result = MagicMock()
    result.scalar.return_value = 0
    result.all.return_value = []
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    payload = await dashboard_endpoint.get_my_day_dashboard(db=db)

    assert isinstance(payload["market_news"], list)
    assert payload["market_news"][0]["title"] == "English headline"
    assert payload["market_news"][0]["content"] == "Body"
