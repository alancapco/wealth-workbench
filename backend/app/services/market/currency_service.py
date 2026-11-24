"""
Currency exchange service using FreeCurrencyAPI (freecurrencyapi.com).
Base currency is USD. Caches live rates for 1 hour.

Without a working live feed the service returns clearly-labelled static
fallback values (source=STATIC_FALLBACK, is_live=False). Callers must surface
those labels so stale rates cannot be presented as live market data.
"""
import time
from datetime import datetime, UTC

import httpx

from app.core.config import settings

FREECURRENCY_BASE = "https://api.freecurrencyapi.com/v1"
CACHE_SECONDS = 3600  # 1 hour

STATIC_FALLBACK_RATES = {
    "USD": 1.0,
    "HKD": 7.84,
    "SGD": 1.28,
    "EUR": 0.90,
    "GBP": 0.75,
    "JPY": 158.5,
    "CNY": 6.68,
    "AUD": 1.46,
}


class CurrencyService:
    def __init__(self):
        self._rates_cache: dict[str, tuple[float, dict, dict]] = {}
        self._meta = self._static_meta()

    @staticmethod
    def _static_meta() -> dict:
        return {
            "source": "STATIC_FALLBACK",
            "as_of": None,  # the vintage of these approximate values is unknown
            "is_live": False,
            "note": "Approximate static reference rates; no dated market snapshot.",
        }

    async def get_latest_rates(self, currencies: str = "HKD,SGD,USD,EUR,GBP,JPY,CNY,AUD") -> dict[str, float]:
        """Get exchange rates with USD as base; the return shape stays a plain rate map."""
        key = currencies
        cached = self._rates_cache.get(key)
        now = time.monotonic()
        if cached and now - cached[0] < CACHE_SECONDS:
            self._meta = cached[2]
            return cached[1]

        if not settings.FREECURRENCY_API_KEY:
            self._meta = self._static_meta()
            return dict(STATIC_FALLBACK_RATES)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{FREECURRENCY_BASE}/latest",
                    params={"apikey": settings.FREECURRENCY_API_KEY, "currencies": currencies}
                )
                resp.raise_for_status()
                data = resp.json().get("data", {})
            data["USD"] = 1.0
            meta = {
                "source": "FREECURRENCYAPI",
                "as_of": datetime.now(UTC).isoformat(),
                "is_live": True,
                "note": None,
            }
            self._rates_cache[key] = (now, data, meta)
            self._meta = meta
            return data
        except Exception:
            # A failed live feed must never be presented as live data.
            self._meta = self._static_meta()
            return dict(STATIC_FALLBACK_RATES)

    async def get_latest_rates_with_metadata(self, currencies: str = "HKD,SGD,USD,EUR,GBP,JPY,CNY,AUD") -> dict:
        """Rate map plus its provenance labels for the currency-exposure response."""
        rates = await self.get_latest_rates(currencies)
        return {"rates": rates, **self._meta}

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
