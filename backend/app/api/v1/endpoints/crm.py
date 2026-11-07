"""
CRM / HubSpot Sync API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Client
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/sync")
async def sync_all_clients_to_hubspot(
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Sync all RM Workbench clients to HubSpot CRM
    Shows diff before applying changes
    """
    try:
        from app.services.crm.crm_service import crm_service
        # Get all clients from database
        result = await db.execute(select(Client))
        clients = result.scalars().all()

        if not clients:
            return {
                "status": "no_clients",
                "message": "No clients found to sync",
                "synced": []
            }

        synced_results = []

        for client in clients:
            try:
                # Prepare client data
                name_parts = client.name.split(' ', 1)
                client_data = {
                    'firstname': name_parts[0] if name_parts else '',
                    'lastname': name_parts[1] if len(name_parts) > 1 else '',
                    'email': client.email,
                    'phone': client.phone,
                    'external_id': client.external_id,
                    'aum': client.aum,
                    'currency': client.currency,
                    'client_type': client.client_type,
                    'region': client.region,
                    'risk_profile': client.risk_profile,
                    'shariah_compliant': client.shariah_compliant,
                    'is_family_office': client.is_family_office
                }

                # Sync to HubSpot
                result = await crm_service.sync_client_to_hubspot(client_data)

                synced_results.append({
                    "client_name": client.name,
                    "action": result['action'],
                    "hubspot_id": result['hubspot_id'],
                    "diff": result.get('diff', {})
                })

                logger.info(f"Synced {client.name}: {result['action']}")

            except Exception as e:
                logger.error(f"Error syncing {client.name}: {e}")
                synced_results.append({
                    "client_name": client.name,
                    "action": "error",
                    "error": str(e)
                })

        return {
            "status": "success",
            "total_clients": len(clients),
            "synced": len([r for r in synced_results if r['action'] != 'error']),
            "errors": len([r for r in synced_results if r['action'] == 'error']),
            "results": synced_results
        }

    except Exception as e:
        logger.error(f"Error syncing clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/{client_id}")
async def sync_single_client_to_hubspot(
    client_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Sync a single client to HubSpot
    """
    try:
        from app.services.crm.crm_service import crm_service
        # Get client
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Prepare client data
        name_parts = client.name.split(' ', 1)
        client_data = {
            'firstname': name_parts[0] if name_parts else '',
            'lastname': name_parts[1] if len(name_parts) > 1 else '',
            'email': client.email,
            'phone': client.phone,
            'external_id': client.external_id,
            'aum': client.aum,
            'currency': client.currency,
            'client_type': client.client_type,
            'region': client.region,
            'risk_profile': client.risk_profile,
            'shariah_compliant': client.shariah_compliant,
            'is_family_office': client.is_family_office
        }

        # Sync to HubSpot
        result = await crm_service.sync_client_to_hubspot(client_data)

        return {
            "status": "success",
            "client_name": client.name,
            "action": result['action'],
            "hubspot_id": result['hubspot_id'],
            "diff": result.get('diff', {})
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing client: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_hubspot_status() -> Dict:
    """
    Check HubSpot connection status
    """
    try:
        from app.services.crm.crm_service import crm_service
        # Try to search for a contact (doesn't matter if found)
        result = await crm_service.find_contact_by_email("test@example.com")

        return {
            "status": "connected",
            "service": "HubSpot CRM",
            "message": "Successfully connected to HubSpot API"
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "HubSpot CRM",
            "message": str(e)
        }
