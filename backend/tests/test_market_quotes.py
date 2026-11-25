"""Alpha Vantage quote / history path (Tiger Broker removed)."""
from unittest.mock import MagicMock

import pytest

from app.core.config import settings
from app.services.market.market_service import MarketDataService


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr(settings, "ALPHAVANTAGE_API_KEY", "test-av-key")
    return MarketDataService()


def test_quotes_configured_tracks_alpha_vantage(monkeypatch):
    monkeypatch.setattr(settings, "ALPHAVANTAGE_API_KEY", "")
    assert MarketDataService().quotes_configured is False
    monkeypatch.setattr(settings, "ALPHAVANTAGE_API_KEY", "key")
    assert MarketDataService().quotes_configured is True


@pytest.mark.asyncio
async def test_quotes_empty_without_alpha_vantage_key(monkeypatch):
    monkeypatch.setattr(settings, "ALPHAVANTAGE_API_KEY", "")
    service = MarketDataService()
    quotes = await service.get_real_time_quote(["AAPL"])
    assert quotes == []


@pytest.mark.asyncio
async def test_quotes_use_alpha_vantage_global_quote(service, monkeypatch):
    payload = {
        "Global Quote": {
            "01. symbol": "HSBC",
            "02. open": "40.0",
            "03. high": "41.0",
            "04. low": "39.5",
            "05. price": "40.5",
            "06. volume": "1000",
            "08. previous close": "40.0",
            "09. change": "0.5",
            "10. change percent": "1.25%",
        }
    }
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    get = MagicMock(return_value=response)
    monkeypatch.setattr("app.services.market.market_service.requests.get", get)

    quotes = await service.get_real_time_quote(["0005.HK"])

    assert len(quotes) == 1
    assert quotes[0]["symbol"] == "0005.HK"
    assert quotes[0]["quoted_symbol"] == "HSBC"
    assert quotes[0]["price"] == 40.5
    assert quotes[0]["source_id"] == "AlphaVantage"
    assert get.call_args.kwargs["params"]["function"] == "GLOBAL_QUOTE"
    assert get.call_args.kwargs["params"]["symbol"] == "HSBC"


@pytest.mark.asyncio
async def test_history_empty_without_key(monkeypatch):
    monkeypatch.setattr(settings, "ALPHAVANTAGE_API_KEY", "")
    service = MarketDataService()
    rows = await service.get_historical_data("AAPL", limit=5)
    assert rows == []


def test_provider_configuration_uses_alpha_vantage(monkeypatch):
    monkeypatch.setattr(settings, "ALPHAVANTAGE_API_KEY", "av")
    assert settings.provider_configuration["market_data"] == "CONFIGURED"
    monkeypatch.setattr(settings, "ALPHAVANTAGE_API_KEY", "")
    assert settings.provider_configuration["market_data"] == "UNCONFIGURED"
