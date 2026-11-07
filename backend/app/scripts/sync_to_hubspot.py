"""
Sync demo clients to HubSpot CRM
"""
import asyncio
from app.services.crm.crm_service import crm_service
from app.core.database import async_session_maker
from sqlalchemy import select
from app.models.models import Client

async def sync_to_hubspot():
    """Sync all demo clients to HubSpot"""
    print("🔄 Starting HubSpot sync...")

    async with async_session_maker() as session:
        # Get all clients
        result = await session.execute(select(Client))
        clients = result.scalars().all()

        print(f"Found {len(clients)} clients to sync")

        for client in clients:
            print(f"\n📤 Syncing: {client.name}")

            try:
                # Check if contact exists in HubSpot
                existing = await crm_service.find_contact_by_email(client.email)

                if existing:
                    print(f"   ℹ️  Contact exists: {existing['id']}")
                    # Update existing contact
                    result = await crm_service.update_contact(
                        existing['id'],
                        {
                            'firstname': client.name.split()[0] if client.name else '',
                            'lastname': ' '.join(client.name.split()[1:]) if client.name and len(client.name.split()) > 1 else '',
                            'email': client.email,
                            'phone': client.phone,
                            'rm_aum': str(client.aum),
                            'rm_currency': client.currency,
                            'rm_client_type': client.client_type,
                            'rm_region': client.region,
                            'rm_risk_profile': client.risk_profile,
                            'rm_external_id': client.external_id,
                            'rm_shariah_compliant': 'Yes' if client.shariah_compliant else 'No',
                            'rm_is_family_office': 'Yes' if client.is_family_office else 'No'
                        }
                    )
                    print(f"   ✅ Updated: {result['id']}")
                else:
                    # Create new contact
                    result = await crm_service.create_contact({
                        'firstname': client.name.split()[0] if client.name else '',
                        'lastname': ' '.join(client.name.split()[1:]) if client.name and len(client.name.split()) > 1 else '',
                        'email': client.email,
                        'phone': client.phone,
                        'rm_aum': str(client.aum),
                        'rm_currency': client.currency,
                        'rm_client_type': client.client_type,
                        'rm_region': client.region,
                        'rm_risk_profile': client.risk_profile,
                        'rm_external_id': client.external_id,
                        'rm_shariah_compliant': 'Yes' if client.shariah_compliant else 'No',
                        'rm_is_family_office': 'Yes' if client.is_family_office else 'No'
                    })
                    print(f"   ✅ Created: {result['id']}")

            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

    print("\n✅ Sync complete!")

if __name__ == "__main__":
    asyncio.run(sync_to_hubspot())
