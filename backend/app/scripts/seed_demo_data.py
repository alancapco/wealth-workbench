"""
Demo Data Seed Script
Seeds the database with synthetic client, portfolio, and interaction data for testing
"""
import asyncio
import uuid
from datetime import datetime, UTC, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.models.models import Client, Holding, Interaction, SourceKind
import random

# Convert to async URL
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def clear_existing_data():
    """Clear existing demo data to allow re-seeding"""
    async with async_session_maker() as session:
        from sqlalchemy import delete
        try:
            # Delete in reverse order of foreign key dependencies
            await session.execute(delete(Interaction))
            await session.execute(delete(Holding))
            await session.execute(delete(Client))
            await session.commit()
            print("🧹 Cleared existing demo data")
        except Exception as e:
            print(f"⚠️  Could not clear existing data: {e}")
            await session.rollback()

async def seed_clients():
    """Seed demo clients"""
    clients_data = [
        {
            "external_id": "RM001-C001",
            "name": "Kenneth Wong",
            "email": "kenneth.wong@example.com",
            "phone": "+852-9876-5432",
            "aum": 45.2e6,
            "currency": "HKD",
            "client_type": "Private Wealth",
            "region": "Hong Kong",
            "risk_profile": "Moderate",
            "shariah_compliant": False,
            "preferences": {
                "rebalancing_frequency": "quarterly",
                "tax_optimization": "gradual_execution",
                "last_rebalancing": "2024-10-15",
                "suitability_expiry": "2025-08-10"
            }
        },
        {
            "external_id": "RM001-C002",
            "name": "Ahmad Rahman",
            "email": "ahmad.rahman@example.com",
            "phone": "+65-9123-4567",
            "aum": 32.8e6,
            "currency": "SGD",
            "client_type": "Private Wealth",
            "region": "Singapore",
            "risk_profile": "Conservative",
            "shariah_compliant": True,
            "preferences": {
                "shariah_standard": "AAOIFI",
                "last_zakat_calculation": "2025-03-16",
                "hawl_start": "2024-03-16"
            }
        },
        {
            "external_id": "RM001-C003",
            "name": "Tan Family Office",
            "email": "tan.family@example.com",
            "phone": "+65-6789-0123",
            "aum": 120.5e6,
            "currency": "SGD",
            "client_type": "Family Office",
            "region": "Singapore",
            "risk_profile": "Balanced",
            "is_family_office": True,
            "shariah_compliant": False,
            "family_entities": [
                {"name": "Patriarch Trust", "entitlement": "full"},
                {"name": "Gen 2 - Son 1", "entitlement": "entity-specific"},
                {"name": "Gen 2 - Daughter 1", "entitlement": "entity-specific"},
                {"name": "Gen 2 - Son 2", "entitlement": "entity-specific"},
                {"name": "Gen 3 - Education Trust 1", "entitlement": "education-only"},
                {"name": "Gen 3 - Education Trust 2", "entitlement": "education-only"},
                {"name": "Operating Company", "entitlement": "restricted"}
            ]
        }
    ]

    async with async_session_maker() as session:
        for client_data in clients_data:
            client = Client(**client_data)
            session.add(client)
        await session.commit()
        print(f"✅ Seeded {len(clients_data)} clients")

async def seed_holdings():
    """Seed demo portfolio holdings"""
    async with async_session_maker() as session:
        # Get Kenneth Wong
        from sqlalchemy import select
        result = await session.execute(
            select(Client).where(Client.external_id == "RM001-C001")
        )
        kenneth = result.scalar_one()

        holdings_data = [
            {"symbol": "0005.HK", "quantity": 10000, "cost_basis": 50.0, "current_value": 2.3e6, "asset_class": "Equity"},
            {"symbol": "00700.HK", "quantity": 5000, "cost_basis": 320.0, "current_value": 1.8e6, "asset_class": "Equity"},
            {"symbol": "0001.HK", "quantity": 15000, "cost_basis": 55.0, "current_value": 1.2e6, "asset_class": "Equity"},
        ]

        for holding_data in holdings_data:
            holding = Holding(
                client_id=kenneth.id,
                source_kind=SourceKind.SEEDED,
                as_of=datetime.now(),
                **holding_data
            )
            session.add(holding)

        await session.commit()
        print(f"✅ Seeded {len(holdings_data)} holdings for Kenneth Wong")

async def seed_interactions():
    """Seed demo interaction history"""
    async with async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Client).where(Client.external_id == "RM001-C001")
        )
        kenneth = result.scalar_one()

        interactions_data = [
            {
                "interaction_date": datetime.now() - timedelta(days=30),
                "interaction_type": "meeting",
                "summary": "Discussed quarterly rebalancing preferences — prefers gradual execution to minimize tax impact",
                "preferences_extracted": [
                    {"key": "rebalancing_approach", "value": "gradual_execution"},
                    {"key": "family_involvement", "value": "daughter_next_meeting"}
                ],
                "action_items": [
                    {"action": "Send consolidated quarterly statement", "due_date": "2024-11-20"}
                ],
                "recording_consent": True,
                "consent_method": "verbal",
                "confidence": 0.95
            },
            {
                "interaction_date": datetime.now() - timedelta(days=60),
                "interaction_type": "meeting",
                "summary": "Expressed interest in Hong Kong tech sector opportunities, specifically fintech",
                "preferences_extracted": [
                    {"key": "sector_interest", "value": "hong_kong_tech"},
                    {"key": "subsector", "value": "fintech"}
                ],
                "recording_consent": True,
                "consent_method": "written",
                "confidence": 0.92
            }
        ]

        for interaction_data in interactions_data:
            interaction = Interaction(
                client_id=kenneth.id,
                source_kind=SourceKind.RM_MANUAL,
                **interaction_data
            )
            session.add(interaction)

        await session.commit()
        print(f"✅ Seeded {len(interactions_data)} interactions")

async def main():
    """Main seed function"""
    print("🌱 Starting database seed...")

    try:
        await clear_existing_data()
        await seed_clients()
        await seed_holdings()
        await seed_interactions()
        print("✅ Database seeding complete!")
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise to allow container to continue starting

if __name__ == "__main__":
    asyncio.run(main())
