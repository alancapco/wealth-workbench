"""
Clients API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Client, Holding
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    aum: float
    currency: str = "USD"
    client_type: str = "Private Wealth"
    risk_profile: str = "Moderate"
    shariah_compliant: bool = False

@router.get("/")
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all clients"""
    try:
        result = await db.execute(
            select(Client).offset(skip).limit(limit)
        )
        clients = result.scalars().all()
        return {"clients": [c.__dict__ for c in clients], "count": len(clients)}
    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{client_id}")
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get client by ID"""
    try:
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return client
    except Exception as e:
        logger.error(f"Error fetching client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{client_id}/portfolio")
async def get_client_portfolio(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get client portfolio holdings"""
    try:
        result = await db.execute(
            select(Holding).where(Holding.client_id == client_id)
        )
        holdings = result.scalars().all()

        return {
            "client_id": client_id,
            "holdings": [h.__dict__ for h in holdings],
            "total_value": sum(h.current_value or 0 for h in holdings)
        }
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{client_id}/shariah-report")
async def get_shariah_report(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate Shariah compliance report for client"""
    try:
        from app.services.shariah.shariah_service import shariah_service
        # Get client portfolio
        result = await db.execute(
            select(Holding).where(Holding.client_id == client_id)
        )
        holdings = result.scalars().all()

        # Screen each holding
        screening_results = []
        for holding in holdings:
            screening = await shariah_service.screen_instrument(
                holding.symbol,
                {"business_description": ""}  # Would fetch from market data
            )
            screening_results.append(screening)

        # Calculate zakat
        portfolio_data = [
            {
                "symbol": h.symbol,
                "current_value": h.current_value,
                "asset_class": h.asset_class
            }
            for h in holdings
        ]

        zakat = await shariah_service.calculate_zakat(
            client_id,
            portfolio_data,
            "2025-01-01"  # Would calculate actual hawl date
        )

        # Generate comprehensive report
        report = await shariah_service.generate_shariah_report(
            client_id,
            screening_results,
            zakat
        )

        return report

    except Exception as e:
        logger.error(f"Error generating Shariah report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
