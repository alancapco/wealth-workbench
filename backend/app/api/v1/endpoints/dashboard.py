"""
Dashboard API Endpoints
Provides data for the RM Dashboard (My Day)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.services.ranking.ranking_service import ranking_service
from app.models.models import Client
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/my-day")
async def get_my_day_dashboard(
    rm_id: str = "RM001",
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get complete My Day dashboard data
    - KPIs (AUM, meetings, actions, performance)
    - Ranked client list
    - Market news
    - Priority actions
    """
    try:
        from app.services.market.market_service import market_data_service
        # Get market signals for ranking
        watch_symbols = ["HSBC", "0005.HK", "00700.HK"]  # HSBC, Tencent
        market_signals = []

        for symbol in watch_symbols:
            signal = await market_data_service.detect_market_signal(symbol, threshold=2.0)
            if signal:
                market_signals.append(signal)

        # Rank clients
        ranked_clients = await ranking_service.rank_clients(
            db=db,
            rm_id=rm_id,
            market_signals=market_signals
        )

        # Get market news
        market_news = await market_data_service.get_market_news(limit=10)

        # Calculate KPIs from database
        from sqlalchemy import func
        from app.models.models import Client

        kpi_result = await db.execute(
            select(func.count(Client.id), func.sum(Client.aum))
        )
        client_count, total_aum = kpi_result.one()

        dashboard_data = {
            "kpis": {
                "total_aum": float(total_aum) if total_aum else 0,
                "total_clients": client_count,
                "meetings_today": 3,  # TODO: Get from calendar
                "open_actions": 7,  # TODO: Get from tasks
                "ytd_performance": 5.8
            },
            "ranked_clients": ranked_clients[:10],  # Top 10
            "market_news": market_news,
            "market_signals": market_signals,
            "priority_actions": [
                {
                    "priority": 1,
                    "title": f"Prepare brief for {ranked_clients[0]['name']}" if ranked_clients else "No actions",
                    "description": f"{ranked_clients[0]['reason']['description']}" if ranked_clients else "",
                    "due": "Before 10:00 AM"
                }
            ] if ranked_clients else [],
            "workflow": {
                "current_stage": "rank.clients",
                "correlation_id": "8f21a4b2"
            }
        }

        return dashboard_data

    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kpis")
async def get_kpis(
    rm_id: str = "RM001",
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get KPI metrics for dashboard cards
    """
    try:
        # TODO: Calculate from database
        return {
            "total_aum": 428.5e6,
            "currency": "USD",
            "client_count": 45,
            "meetings_today": 3,
            "open_actions": 7,
            "actions_overdue": 2,
            "ytd_performance": 5.8,
            "benchmark_performance": 4.6
        }
    except Exception as e:
        logger.error(f"Error getting KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/book-stats")
async def get_book_stats(
    rm_id: str = "RM001",
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get RM book statistics
    """
    try:
        return {
            "total_clients": 45,
            "family_offices": 8,
            "avg_aum": 9.5e6,
            "meetings_mtd": 18,
            "net_new_assets_ytd": 38e6
        }
    except Exception as e:
        logger.error(f"Error getting book stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/allocation")
async def get_portfolio_allocation(
    rm_id: str = "RM001"
) -> Dict:
    """
    Get aggregated portfolio allocation across RM's book
    """
    try:
        return {
            "equities": 62.0,
            "fixed_income": 28.0,
            "cash": 10.0,
            "breakdown": [
                {"asset_class": "Equities", "percentage": 62.0, "value": 265.7e6},
                {"asset_class": "Fixed Income", "percentage": 28.0, "value": 120.0e6},
                {"asset_class": "Cash", "percentage": 10.0, "value": 42.8e6}
            ]
        }
    except Exception as e:
        logger.error(f"Error getting allocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-trend")
async def get_performance_trend(
    rm_id: str = "RM001",
    period: str = "ytd"
) -> Dict:
    """
    Get performance trend data for charting
    """
    try:
        # Mock YTD performance data
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
        portfolio = [0, 1.2, 2.5, 3.8, 4.2, 4.6, 5.1, 5.5, 5.8]
        benchmark = [0, 0.8, 1.9, 2.8, 3.2, 3.5, 3.9, 4.2, 4.6]

        return {
            "period": period,
            "labels": months,
            "datasets": [
                {
                    "name": "Portfolio",
                    "data": portfolio
                },
                {
                    "name": "Benchmark",
                    "data": benchmark
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error getting performance trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))
