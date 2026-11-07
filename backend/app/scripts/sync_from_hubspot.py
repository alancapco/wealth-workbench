"""
HubSpot Data Sync Script
Syncs contacts from HubSpot to local database
Implements G-11: HubSpot CRM sync integration
"""
import asyncio
from app.services.crm.crm_service import crm_service
from app.core.database import async_session_maker
from sqlalchemy import select
from app.models.models import Client
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_from_hubspot():
    """
    Sync contacts from HubSpot to local database
    Creates or updates clients based on HubSpot data
    """
    logger.info("🔄 Starting HubSpot → Database sync...")

    async with async_session_maker() as session:
        try:
            # Fetch contacts from HubSpot
            contacts = await crm_service.fetch_contacts_from_hubspot(limit=100)

            if not contacts:
                logger.warning("No contacts fetched from HubSpot")
                return

            logger.info(f"Fetched {len(contacts)} contacts from HubSpot")

            created_count = 0
            updated_count = 0

            for contact in contacts:
                props = contact.get("properties", {})
                email = props.get("email")

                if not email:
                    continue

                # Check if client exists
                result = await session.execute(
                    select(Client).where(Client.email == email)
                )
                existing_client = result.scalar_one_or_none()

                if existing_client:
                    # Update existing
                    existing_client.name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
                    existing_client.phone = props.get("phone")
                    existing_client.aum = float(props.get("rm_aum", 0)) if props.get("rm_aum") else None
                    existing_client.currency = props.get("rm_currency", "USD")
                    existing_client.client_type = props.get("rm_client_type")
                    existing_client.region = props.get("rm_region")
                    existing_client.risk_profile = props.get("rm_risk_profile")
                    updated_count += 1
                else:
                    # Create new
                    new_client = Client(
                        id=uuid.uuid4(),
                        external_id=props.get("rm_external_id"),
                        name=f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                        email=email,
                        phone=props.get("phone"),
                        aum=float(props.get("rm_aum", 0)) if props.get("rm_aum") else None,
                        currency=props.get("rm_currency", "USD"),
                        client_type=props.get("rm_client_type"),
                        region=props.get("rm_region"),
                        risk_profile=props.get("rm_risk_profile")
                    )
                    session.add(new_client)
                    created_count += 1

            await session.commit()
            logger.info(f"✅ Sync complete: {created_count} created, {updated_count} updated")

        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(sync_from_hubspot())
