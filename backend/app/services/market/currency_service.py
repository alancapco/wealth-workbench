"""
Currency exchange service using FreeCurrencyAPI (freecurrencyapi.com).
Base currency is USD. Caches rates for 1 hour.
"""
import time
import httpx
from app.core.config import settings

FREECURRENCY_BASE = "https://api.freecurrencyapi.com/v1"
CACHE_SECONDS = 3600  # 1 hour


class CurrencyService:
    def __init__(self):
        self._rates_cache: dict[str, tuple[float, dict]] = {}

    async def get_latest_rates(self, currencies: str = "HKD,SGD,USD,EUR,GBP,JPY,CNY,AUD") -> dict[str, float]:
        """Get latest exchange rates with USD as base."""
        key = currencies
        cached = self._rates_cache.get(key)
        now = time.monotonic()
        if cached and now - cached[0] < CACHE_SECONDS:
            return cached[1]

        api_key = settings.FREECURRENCY_API_KEY
        if not api_key:
            # Fallback: return approximate static rates
            return {"USD": 1.0, "HKD": 7.84, "SGD": 1.28, "EUR": 0.90, "GBP": 0.75, "JPY": 158.5, "CNY": 6.68, "AUD": 1.46}

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{FREECURRENCY_BASE}/latest",
                params={"apikey": api_key, "currencies": currencies}
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            # Always include USD = 1.0
            data["USD"] = 1.0
            self._rates_cache[key] = (now, data)
            return data

    async def convert_to_usd(self, amount: float, from_currency: str, rates: dict[str, float] = None) -> float:
        """Convert an amount from given currency to USD."""
        if from_currency == "USD":
            return amount
        if rates is None:
            rates = await self.get_latest_rates()
        rate = rates.get(from_currency, 1.0)
        return amount / rate if rate else amount

    async def convert_from_usd(self, amount_usd: float, to_currency: str, rates: dict[str, float] = None) -> float:
        """Convert USD amount to target currency."""
        if to_currency == "USD":
            return amount_usd
        if rates is None:
            rates = await self.get_latest_rates()
        rate = rates.get(to_currency, 1.0)
        return amount_usd * rate


currency_service = CurrencyService()
