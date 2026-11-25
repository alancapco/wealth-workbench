"""
Market Data API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
import logging

from app.services.market.market_service import market_data_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/quotes")
async def get_quotes(
    symbols: str = Query(..., description="Comma-separated list of symbols")
):
    """Get real-time quotes for symbols"""
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        quotes = await market_data_service.get_real_time_quote(symbol_list)
        return {"quotes": quotes}
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news")
async def get_market_news(
    symbols: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    lang: Optional[str] = Query(None, description="Accepted for compatibility; news is English-only"),
):
    """Get English market news with caching. Returns source, cached flag, and as_of timestamp."""
    try:
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else None
        news, source, cached = await market_data_service.get_market_news(
            symbol_list or None, limit, lang=lang
        )
        return {
            "news": news,
            "count": len(news),
            "source": source,
            "cached": cached,
            "as_of": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/snapshot")
async def get_quotes_snapshot():
    """Get quotes for a fixed set of HK-relevant tickers."""
    try:
        quotes = await market_data_service.get_market_quotes_snapshot()
        return {"quotes": quotes, "count": len(quotes)}
    except Exception as e:
        logger.error(f"Error fetching snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals")
async def detect_signals(
    symbols: str = Query(..., description="Comma-separated symbols to monitor"),
    threshold: float = Query(2.0, ge=0.5, le=10.0)
):
    """Detect significant market movements"""
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        signals = []
        for symbol in symbol_list:
            signal = await market_data_service.detect_market_signal(symbol, threshold)
            if signal:
                signals.append(signal)
        return {"signals": signals, "count": len(signals)}
    except Exception as e:
        logger.error(f"Error detecting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    period: str = Query("1d", description="Period: 1d, 1w, 1m, etc"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get historical price data for charting"""
    try:
        data = await market_data_service.get_historical_data(symbol, period, limit)
        return {"symbol": symbol, "data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mode")
async def set_market_mode(mode: str):
    """Switch between LIVE and REPLAY mode"""
    try:
        market_data_service.set_mode(mode)
        return {"mode": mode, "status": "updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
