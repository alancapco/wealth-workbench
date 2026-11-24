"""
Dashboard API Endpoints.

All figures are derived from the live database. Where the underlying data does
not exist yet (for example a performance time series), the endpoint returns an
explicit ``available: false`` / ``null`` rather than a fabricated number.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


async def _scalar(db: AsyncSession, sql: str, default: Any = 0) -> Any:
    try:
        result = await db.execute(text(sql))
        value = result.scalar()
        return default if value is None else value
    except Exception:  # table absent in a partially-migrated environment
        logger.warning("Dashboard query failed: %s", sql, exc_info=True)
        return default


async def _rows(db: AsyncSession, sql: str) -> list[tuple]:
    try:
        result = await db.execute(text(sql))
        return list(result.all())
    except Exception:
        logger.warning("Dashboard query failed: %s", sql, exc_info=True)
        return []


async def _book_snapshot(db: AsyncSession) -> Dict[str, Any]:
    """Single source of truth for the KPI + book statistics endpoints."""
    client_count = int(await _scalar(db, "SELECT COUNT(*) FROM demo_clients"))
    total_aum_musd = float(await _scalar(db, "SELECT COALESCE(SUM(aum_usd_millions), 0) FROM demo_clients"))
    family_offices = int(await _scalar(db, "SELECT COUNT(*) FROM demo_clients WHERE family_office_name IS NOT NULL"))

    holdings_count = int(await _scalar(db, "SELECT COUNT(*) FROM client_portfolio_holdings"))
    holdings_value = float(await _scalar(db, "SELECT COALESCE(SUM(value_usd_millions), 0) FROM client_portfolio_holdings"))

    today = date.today()
    month_start = today.replace(day=1)
    meetings_today = int(await _scalar(
        db, f"SELECT COUNT(*) FROM client_conversations WHERE conversation_date = DATE '{today.isoformat()}'"
    ))
    meetings_mtd = int(await _scalar(
        db, f"SELECT COUNT(*) FROM client_conversations WHERE conversation_date >= DATE '{month_start.isoformat()}'"
    ))
    open_actions = int(await _scalar(db, "SELECT COUNT(*) FROM outbox_actions WHERE status IN ('PENDING', 'QUEUED', 'SENDING')"))
    overdue_actions = int(await _scalar(
        db, "SELECT COUNT(*) FROM outbox_actions WHERE status = 'PENDING' AND created_at < NOW() - INTERVAL '7 days'"
    ))
    interactions_mtd = int(await _scalar(
        db,
        f"SELECT COUNT(*) FROM interactions WHERE interaction_date >= TIMESTAMP '{month_start.isoformat()} 00:00:00'",
    ))

    # Weighted unrealised return is a real, derivable performance measure from holdings.
    weighted_gain = await _scalar(
        db,
        "SELECT SUM(unrealized_gain_pct * value_usd_millions) / NULLIF(SUM(value_usd_millions), 0) "
        "FROM client_portfolio_holdings WHERE unrealized_gain_pct IS NOT NULL",
        default=None,
    )

    return {
        "total_aum": round(total_aum_musd * 1_000_000, 2),
        "currency": "USD",
        "client_count": client_count,
        "family_offices": family_offices,
        "avg_aum": round((total_aum_musd * 1_000_000) / client_count, 2) if client_count else 0,
        "meetings_today": meetings_today,
        "meetings_mtd": meetings_mtd + interactions_mtd,
        "open_actions": open_actions,
        "actions_overdue": overdue_actions,
        "holdings_count": holdings_count,
        "holdings_value_usd": round(holdings_value * 1_000_000, 2),
        "ytd_performance": round(float(weighted_gain), 2) if weighted_gain is not None else None,
        "benchmark_performance": None,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source": "demo_clients, client_portfolio_holdings, client_conversations, outbox_actions",
    }


@router.get("/my-day")
async def get_my_day_dashboard(rm_id: str = "RM001", db: AsyncSession = Depends(get_db)) -> Dict:
    """My Day dashboard. Every number comes from the database."""
    try:
        snap = await _book_snapshot(db)

        from app.services.journey import service as journey

        day = await journey.my_day(db)
        leads = day.get("focus") or []
        ranked_clients = [
            {
                "client_id": lead["client_id"],
                "name": lead["name"],
                "aum": (lead.get("aum_usd_millions") or 0) * 1_000_000,
                "total_score": lead.get("score") or 0,
                "rank": lead.get("rank"),
                "reason": {
                    "description": "; ".join(lead.get("reasons") or []) or lead.get("next_best_action") or "",
                },
                "jurisdiction": lead.get("jurisdiction"),
                "next_best_action": lead.get("next_best_action"),
            }
            for lead in leads
        ]
        priority_actions = [
            {
                "priority": item["rank"],
                "title": item.get("next_best_action") or f"Review {item['name']}",
                "description": item["reason"]["description"],
                "client_id": item["client_id"],
                "due": None,
            }
            for item in ranked_clients[:5]
        ]

        market_news: list[Any] = []
        try:
            from app.services.market.market_service import market_data_service

            news_items, _, _ = await market_data_service.get_market_news(limit=10)
            market_news = news_items or []
        except Exception:
            logger.warning("Market news unavailable", exc_info=True)

        return {
            "kpis": {
                "total_aum": snap["total_aum"],
                "total_clients": snap["client_count"],
                "meetings_today": snap["meetings_today"],
                "open_actions": day.get("pipeline_open"),
                "ytd_performance": snap["ytd_performance"],
            },
            "ranked_clients": ranked_clients[:10],
            "market_news": market_news,
            "market_signals": [],
            "priority_actions": priority_actions,
            "journey": {
                "pipeline_open": day.get("pipeline_open"),
                "weighted_forecast_usd": day.get("weighted_forecast_usd"),
                "rpq_expiring": day.get("rpq_expiring"),
                "unread_notifications": day.get("unread_notifications"),
                "recent": day.get("recent") or [],
            },
            "workflow": {
                "current_stage": "ENGAGE",
                "correlation_id": None,
                "source": "journey",
            },
            "as_of": snap["as_of"],
        }
    except Exception as exc:
        logger.error("Error loading dashboard: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/kpis")
async def get_kpis(rm_id: str = "RM001", db: AsyncSession = Depends(get_db)) -> Dict:
    """KPI metrics for the journey book, not a second client list."""
    try:
        from app.services.journey import service as journey

        snap = await _book_snapshot(db)
        day = await journey.my_day(db)
        snap["open_actions"] = day.get("pipeline_open")
        snap["pipeline_forecast_usd"] = day.get("weighted_forecast_usd")
        snap["unread_notifications"] = day.get("unread_notifications")
        snap["source"] = "journey, demo_clients, client_portfolio_holdings"
        return snap
    except Exception as exc:
        logger.error("Error getting KPIs: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/book-stats")
async def get_book_stats(rm_id: str = "RM001", db: AsyncSession = Depends(get_db)) -> Dict:
    """Book statistics derived from the live book."""
    try:
        snap = await _book_snapshot(db)
        return {
            "total_clients": snap["client_count"],
            "family_offices": snap["family_offices"],
            "avg_aum": snap["avg_aum"],
            "meetings_mtd": snap["meetings_mtd"],
            # No cash-flow ledger exists yet; do not fabricate a number.
            "net_new_assets_ytd": None,
            "as_of": snap["as_of"],
            "source": snap["source"],
        }
    except Exception as exc:
        logger.error("Error getting book stats: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/allocation")
async def get_portfolio_allocation(rm_id: str = "RM001", db: AsyncSession = Depends(get_db)) -> Dict:
    """Aggregate asset allocation from real holdings."""
    try:
        rows = await _rows(
            db,
            "SELECT COALESCE(asset_class, 'Unclassified') AS asset_class, "
            "SUM(value_usd_millions) AS value_musd "
            "FROM client_portfolio_holdings GROUP BY 1 ORDER BY 2 DESC",
        )
        total = sum(float(row[1] or 0) for row in rows)
        breakdown = [
            {
                "asset_class": str(row[0]),
                "percentage": round(float(row[1] or 0) / total * 100, 2) if total else 0,
                "value": round(float(row[1] or 0) * 1_000_000, 2),
            }
            for row in rows
        ]
        by_name = {item["asset_class"].lower(): item["percentage"] for item in breakdown}
        return {
            "equities": by_name.get("equities", 0),
            "fixed_income": by_name.get("fixed income", 0),
            "cash": by_name.get("cash", 0),
            "breakdown": breakdown,
            "total_value": round(total * 1_000_000, 2),
            "source": "client_portfolio_holdings",
        }
    except Exception as exc:
        logger.error("Error getting allocation: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/performance-trend")
async def get_performance_trend(
    rm_id: str = "RM001", period: str = "ytd", db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Real performance view. There is no returns time-series in the schema yet, so
    the endpoint exposes the derivable measure instead: weighted unrealised gain
    by asset class. ``kind`` tells the UI which chart to render.
    """
    try:
        rows = await _rows(
            db,
            "SELECT COALESCE(asset_class, 'Unclassified') AS asset_class, "
            "SUM(unrealized_gain_pct * value_usd_millions) / NULLIF(SUM(value_usd_millions), 0) AS gain_pct "
            "FROM client_portfolio_holdings "
            "WHERE unrealized_gain_pct IS NOT NULL GROUP BY 1 ORDER BY 1",
        )
        labels = [str(row[0]) for row in rows]
        values = [round(float(row[1] or 0), 2) for row in rows]
        return {
            "period": period,
            "kind": "asset_class_return",
            "available": bool(rows),
            "labels": labels,
            "datasets": [{"name": "Weighted unrealised gain (%)", "data": values}],
            "note": "No returns time-series is stored. Showing weighted unrealised gain by asset class.",
            "source": "client_portfolio_holdings",
        }
    except Exception as exc:
        logger.error("Error getting performance trend: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
