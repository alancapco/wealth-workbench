"""
Demo Data Seed Script
Seeds the database with synthetic client, portfolio, and interaction data for testing
"""
import asyncio
import hashlib
import json
import uuid
from datetime import date, datetime, UTC, timedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.core.identity import FIXTURE_TENANT_ID
from app.models.models import Client, Holding, Interaction
from app.models.memory import ClientMemoryRecord
from app.models.client_data import ClientConversation, DemoClient
from app.models.platform import ClientScope
from app.models.workflow import Workflow
from app.models.artifact import ArtifactLineage, ArtifactRevision
import random

FIXTURE_ENVIRONMENT_ID = "fixture-test-env"
FIXTURE_BOOKS = ("FIXTURE_BOOK_001", "FIXTURE_BOOK_002")
FIXTURE_ENTITLEMENT_REVISION = "fixture-rev-001"

# Declared ownership / beneficiary structure for the Tan Family Office demo.
# This is the same hierarchy that used to be hardcoded inside the frontend
# FamilyGraphModal; it now lives in the data layer so the family-graph API can
# serve real, structured rows instead of placeholder node names.
#
# `parent` is an EXPLICIT declared link to another entity's name. It is never
# inferred from the display name. An absent parent means the entity hangs off
# the household root. `entitlement` and `kind` are descriptive metadata only —
# no AUM or ownership percentage is invented.
FAMILY_OFFICE_ENTITIES = [
    {"name": "Patriarch Trust", "entitlement": "full", "kind": "TRUST", "parent": None},
    {"name": "Gen 2 - Son 1", "entitlement": "entity-specific", "kind": "PERSON", "parent": "Patriarch Trust"},
    {"name": "Gen 2 - Daughter 1", "entitlement": "entity-specific", "kind": "PERSON", "parent": "Patriarch Trust"},
    {"name": "Gen 2 - Son 2", "entitlement": "entity-specific", "kind": "PERSON", "parent": "Patriarch Trust"},
    {"name": "Gen 3 - Education Trust 1", "entitlement": "education-only", "kind": "TRUST", "parent": "Gen 2 - Son 1"},
    {"name": "Gen 3 - Education Trust 2", "entitlement": "education-only", "kind": "TRUST", "parent": "Gen 2 - Daughter 1"},
    {"name": "Operating Company", "entitlement": "restricted", "kind": "COMPANY", "parent": "Patriarch Trust"},
]


async def seed_fixture_environment():
    """Ensure the local fixture tenant and books exist before any FK-constrained write.

    Under AUTH_MODE=fixture the principal is issued for FIXTURE_TENANT_001 with two
    books, but those rows are identity/reference data, not demo client data. Without
    them every telemetry, audit, workflow and action insert fails with a foreign-key
    violation. Idempotent: never overwrites an existing row. Development only.
    """
    if settings.AUTH_MODE.lower() != "fixture":
        print("Skipping fixture environment seed (AUTH_MODE is not fixture)")
        return

    async with async_session_maker() as session:
        await session.execute(
            text(
                "INSERT INTO workbench_tenants "
                "(tenant_id, environment_kind, environment_id, identity_config_ref, created_at) "
                "VALUES (:tenant_id, 'FIXTURE', :environment_id, :revision, now()) "
                "ON CONFLICT (tenant_id) DO NOTHING"
            ),
            {
                "tenant_id": FIXTURE_TENANT_ID,
                "environment_id": FIXTURE_ENVIRONMENT_ID,
                "revision": FIXTURE_ENTITLEMENT_REVISION,
            },
        )
        for book_id in FIXTURE_BOOKS:
            await session.execute(
                text(
                    "INSERT INTO books "
                    "(tenant_id, book_id, source_version, entitlement_revision) "
                    "VALUES (:tenant_id, :book_id, :revision, :revision) "
                    "ON CONFLICT (tenant_id, book_id) DO NOTHING"
                ),
                {
                    "tenant_id": FIXTURE_TENANT_ID,
                    "book_id": book_id,
                    "revision": FIXTURE_ENTITLEMENT_REVISION,
                },
            )
        await session.commit()
        print(f"Ensured fixture tenant {FIXTURE_TENANT_ID} and {len(FIXTURE_BOOKS)} books")

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
            "family_entities": FAMILY_OFFICE_ENTITIES,
        }
    ]

    async with async_session_maker() as session:
        for client_data in clients_data:
            client = Client(**client_data)
            session.add(client)
        await session.commit()
        print(f"✅ Seeded {len(clients_data)} clients")


async def sync_family_office_entities():
    """Idempotently align an EXISTING Tan Family Office row with the seed definition.

    `main()` calls `clear_existing_data()`, which deletes every client, holding and
    interaction. Databases seeded before `family_entities` was introduced still have
    RM001-C003 with `is_family_office=false` and an empty entity list, so the family
    graph endpoint can only return a placeholder node. This targeted update restores
    the declared structure without deleting or recreating any row. It touches only
    `external_id == 'RM001-C003'` and is safe to run repeatedly.
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(Client).where(Client.external_id == "RM001-C003")
        )
        client = result.scalar_one_or_none()
        if client is None:
            print("No RM001-C003 row found; nothing to sync")
            return
        before = (client.is_family_office, len(client.family_entities or []))
        client.is_family_office = True
        client.family_entities = FAMILY_OFFICE_ENTITIES
        await session.commit()
        print(
            f"Synced RM001-C003: is_family_office {before[0]} -> {client.is_family_office}, "
            f"family_entities {before[1]} -> {len(client.family_entities)}"
        )


async def sync_fixture_client_tenants():
    """Assign the fixture tenant to legacy seeded clients with a NULL tenant_id.

    family_relationships / household_groups / household_memberships use
    composite FKs on (tenant_id, client_id) -> clients(tenant_id, id). Older
    seed runs left clients.tenant_id NULL, so every POST into those tables
    failed with ForeignKeyViolationError -> HTTP 500. Idempotent and scoped to
    the three RM001-* demo rows only; never deletes anything.
    """
    external_ids = ("RM001-C001", "RM001-C002", "RM001-C003")
    async with async_session_maker() as session:
        result = await session.execute(
            select(Client).where(
                Client.external_id.in_(external_ids),
                Client.tenant_id.is_(None),
            )
        )
        rows = list(result.scalars().all())
        for client in rows:
            client.tenant_id = FIXTURE_TENANT_ID
        await session.commit()
        print(f"Assigned {FIXTURE_TENANT_ID} to {len(rows)} legacy client row(s)")

async def seed_holdings():
    """Seed demo portfolio holdings"""
    async with async_session_maker() as session:
        # Get Kenneth Wong
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
        # Get Kenneth Wong
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
                # interactions.source_kind is a plain String column; the old
                # SourceKind enum was removed from the models during a refactor.
                source_kind="rm_manual",
                **interaction_data
            )
            session.add(interaction)

        await session.commit()
        print("✅ Seeded 2 interactions")


# ---------------------------------------------------------------------------
# Client memory + conversation fixture data (API-013 / API-014)
# ---------------------------------------------------------------------------
# These are DEMO fixtures, not real client facts. Every row carries a
# `fixture:` marker so the sync functions can be re-run safely and so the data
# is never mistaken for a sourced RM observation.
#
# All three sync_* functions below are idempotent, insert-only and scoped to
# their own marker rows. Unlike main(), NONE of them calls clear_existing_data().

MEMORY_SOURCE_PREFIX = "fixture:"
CONVERSATION_SOURCE_KIND = "fixture:conversation-demo"
DEMO_CONVERSATION_NOTE_PREFIX = "fixture:capco-demo-conversation"
FIXTURE_RM_SUBJECT = "fixture:rm001@example.test"

# (external_id, entry_type, content, source_ref, confidence) — CONFIRMED facts.
CLIENT_MEMORY_FIXTURE = [
    # Ahmad Rahman (RM001-C002)
    ("RM001-C002", "PREFERENCE", "Prefers quarterly portfolio reviews, held in the first week of each quarter.", "fixture:meeting-2026-10-14", "high"),
    ("RM001-C002", "CONSTRAINT", "Portfolio must remain AAOIFI Shariah-compliant; no conventional interest-bearing instruments.", "fixture:onboarding-2026-08-02", "high"),
    ("RM001-C002", "PREFERENCE", "Prefers a written English summary before each meeting; declines unsolicited product pitches.", "fixture:call-2026-09-18", "medium"),
    ("RM001-C002", "GOAL", "Fund two children's overseas education from 2031 while preserving capital in SGD.", "fixture:meeting-2026-10-14", "medium"),
    ("RM001-C002", "FACT", "Based in Singapore; reporting currency SGD; conservative risk profile; AUM SGD 32.8m.", "fixture:crm-record", "high"),
    # Tan Family Office (RM001-C003)
    ("RM001-C003", "FACT", "Multi-generational family office: three Gen-2 branches and two Gen-3 education trusts.", "fixture:household-graph", "high"),
    ("RM001-C003", "CONSTRAINT", "Entity-level data entitlements apply; Gen-2 members see only their own entities.", "fixture:entitlement-review-2026-09-01", "high"),
    ("RM001-C003", "PREFERENCE", "Consolidated monthly reporting with look-through exposure by legal entity.", "fixture:meeting-2026-09-30", "medium"),
    ("RM001-C003", "GOAL", "Succession planning for the operating company, target completion 2028.", "fixture:meeting-2026-09-30", "medium"),
    # Kenneth Wong (RM001-C001)
    ("RM001-C001", "PREFERENCE", "Prefers gradual rebalancing to minimise tax impact rather than a single switch.", "fixture:meeting-2026-10-23", "high"),
    ("RM001-C001", "PREFERENCE", "Interested in Hong Kong technology exposure, specifically fintech.", "fixture:meeting-2026-10-08", "medium"),
    ("RM001-C001", "FACT", "Daughter may join the next review meeting; include her in succession discussions.", "fixture:meeting-2026-10-23", "medium"),
    ("RM001-C001", "PREFERENCE", "Prefers half-yearly in-person reviews in Hong Kong.", "fixture:call-2026-11-05", "medium"),
]

# (external_id, entry_type, content, source_ref) — proposals awaiting RM review.
CLIENT_MEMORY_PROPOSAL_FIXTURE = [
    ("RM001-C002", "PREFERENCE", "Would like meeting agendas shared at least 48 hours in advance.", "fixture:call-2026-11-09"),
    ("RM001-C003", "CONSTRAINT", "Requests a separate consolidated report for the two education trusts.", "fixture:meeting-2026-11-06"),
]

# (external_id, days_ago, interaction_type, summary, preferences, actions, confidence)
CLIENT_CONVERSATION_FIXTURE = [
    ("RM001-C002", 0, "call", "Quarterly review call. Confirmed AAOIFI screening remains in force and agreed to keep SGD as reporting currency.",
     [{"key": "review_cadence", "value": "quarterly"}, {"key": "shariah_standard", "value": "AAOIFI"}],
     ["Send written portfolio summary", "Book Q1 review in first week of January"], 0.94),
    ("RM001-C002", 26, "meeting", "Reviewed education funding goal for two children from 2031. Client asked to preserve capital in SGD.",
     [{"key": "goal", "value": "education_2031"}, {"key": "capital_preservation", "value": "SGD"}],
     ["Prepare education funding projection"], 0.91),
    ("RM001-C002", 52, "call", "Client requested written English summaries before meetings and asked not to receive unsolicited product pitches.",
     [{"key": "communication", "value": "written_english_pre_read"}, {"key": "contact_policy", "value": "no_unsolicited_pitches"}],
     ["Update contact policy"], 0.88),
    ("RM001-C002", 99, "meeting", "Onboarding. Established Shariah-compliant mandate under AAOIFI and conservative risk profile.",
     [{"key": "mandate", "value": "shariah_compliant"}, {"key": "risk_profile", "value": "conservative"}],
     ["File signed mandate"], 0.96),
    ("RM001-C003", 3, "meeting", "Family council review. Agreed monthly consolidated reporting with look-through exposure by legal entity.",
     [{"key": "reporting_cadence", "value": "monthly"}, {"key": "look_through", "value": "by_legal_entity"}],
     ["Configure consolidated report pack"], 0.93),
    ("RM001-C003", 38, "meeting", "Reviewed entity-level entitlements for Gen-2 branches and the two education trusts.",
     [{"key": "entitlements", "value": "entity_level"}],
     ["Confirm entitlement matrix with compliance"], 0.89),
    ("RM001-C001", 4, "call", "Follow-up on gradual rebalancing plan. Client confirmed he prefers phased execution to limit tax impact.",
     [{"key": "rebalancing_approach", "value": "gradual_execution"}],
     ["Produce phased rebalancing schedule"], 0.92),
    ("RM001-C001", 17, "meeting", "Discussed Hong Kong technology and fintech exposure; daughter may join the next review.",
     [{"key": "sector_interest", "value": "hong_kong_tech"}, {"key": "family_involvement", "value": "daughter_next_meeting"}],
     ["Prepare fintech opportunity note"], 0.87),
]

# (days_ago, channel, summary, sentiment, action_items, next_steps)
DEMO_CONVERSATION_FIXTURE = [
    (0, "meeting", "Quarterly portfolio review; agreed to keep current allocation and revisit after year-end.", "neutral",
     ["Send updated allocation sheet"], "Follow up in December"),
    (0, "call", "Checked liquidity requirements for an upcoming property purchase.", "positive",
     ["Confirm cash buffer"], "RM to confirm within 48 hours"),
    (5, "meeting", "Reviewed Shariah-compliant mandate and screening exceptions.", "positive",
     ["Share screening report"], "Annual review in Q1"),
    (12, "call", "Discussed education funding timeline and risk tolerance.", "neutral",
     ["Update financial plan"], "Schedule planning session"),
    (20, "meeting", "Introduced consolidated family reporting and entity-level entitlements.", "positive",
     ["Configure report pack"], "Confirm household structure"),
]


async def sync_client_memory_records():
    """Insert CONFIRMED memory facts and a few NEEDS_REVIEW proposals.

    Idempotent: if any fixture-marked memory row already exists the whole
    function is a no-op. Insert-only — never deletes user-created proposals.
    """
    async with async_session_maker() as session:
        existing = await session.execute(
            select(ClientMemoryRecord.id).where(
                ClientMemoryRecord.source_ref.like(f"{MEMORY_SOURCE_PREFIX}%")
            ).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            print("Client memory fixtures already present; skipping")
            return

        client_rows = await session.execute(
            select(Client).where(Client.external_id.in_({
                row[0] for row in CLIENT_MEMORY_FIXTURE + CLIENT_MEMORY_PROPOSAL_FIXTURE
            }))
        )
        by_external = {c.external_id: c for c in client_rows.scalars().all()}

        now = datetime.now(UTC)
        inserted = 0
        for external_id, entry_type, content, source_ref, confidence in CLIENT_MEMORY_FIXTURE:
            client = by_external.get(external_id)
            if client is None:
                continue
            session.add(ClientMemoryRecord(
                id=uuid.uuid4(),
                tenant_id=client.tenant_id or FIXTURE_TENANT_ID,
                client_id=client.id,
                entry_type=entry_type,
                content=content,
                source_ref=source_ref,
                state="CONFIRMED",
                confidence=confidence,
                proposed_by=FIXTURE_RM_SUBJECT,
                proposed_at=now - timedelta(days=30),
                reviewed_by=FIXTURE_RM_SUBJECT,
                reviewed_at=now - timedelta(days=29),
                review_note="Confirmed during fixture onboarding",
                created_at=now,
            ))
            inserted += 1

        for external_id, entry_type, content, source_ref in CLIENT_MEMORY_PROPOSAL_FIXTURE:
            client = by_external.get(external_id)
            if client is None:
                continue
            session.add(ClientMemoryRecord(
                id=uuid.uuid4(),
                tenant_id=client.tenant_id or FIXTURE_TENANT_ID,
                client_id=client.id,
                entry_type=entry_type,
                content=content,
                source_ref=source_ref,
                state="NEEDS_REVIEW",
                confidence=None,
                proposed_by=FIXTURE_RM_SUBJECT,
                proposed_at=now,
                created_at=now,
            ))
            inserted += 1

        await session.commit()
        print(f"Seeded {inserted} client memory records "
              f"({len(CLIENT_MEMORY_FIXTURE)} confirmed, {len(CLIENT_MEMORY_PROPOSAL_FIXTURE)} pending)")


async def sync_client_conversations():
    """Insert RM meeting / call notes into the `interactions` table.

    Idempotent and insert-only. The two pre-existing Kenneth Wong interactions
    are left untouched; these rows are tagged with a distinct fixture source.
    """
    async with async_session_maker() as session:
        existing = await session.execute(
            select(Interaction.id).where(
                Interaction.source_kind == CONVERSATION_SOURCE_KIND
            ).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            print("Client conversation fixtures already present; skipping")
            return

        client_rows = await session.execute(
            select(Client).where(Client.external_id.in_({
                row[0] for row in CLIENT_CONVERSATION_FIXTURE
            }))
        )
        by_external = {c.external_id: c for c in client_rows.scalars().all()}

        inserted = 0
        for external_id, days_ago, interaction_type, summary, prefs, actions, confidence in CLIENT_CONVERSATION_FIXTURE:
            client = by_external.get(external_id)
            if client is None:
                continue
            session.add(Interaction(
                id=uuid.uuid4(),
                client_id=client.id,
                interaction_date=datetime.now() - timedelta(days=days_ago),
                interaction_type=interaction_type,
                summary=summary,
                preferences_extracted=prefs,
                action_items=actions,
                recording_consent=True,
                consent_method="written",
                source_kind=CONVERSATION_SOURCE_KIND,
                confidence=confidence,
                created_at=datetime.now(),
            ))
            inserted += 1

        await session.commit()
        print(f"Seeded {inserted} client conversation notes")


async def sync_demo_client_conversations():
    """Seed `client_conversations` so dashboard meeting KPIs are not always zero.

    This table belongs to the demo-client universe (FK -> demo_clients.id), so
    it is separate from the RM-client `interactions` seeded above.
    Idempotent and insert-only, tagged via rm_notes.
    """
    async with async_session_maker() as session:
        existing = await session.execute(
            select(ClientConversation.id).where(
                ClientConversation.rm_notes.like(f"{DEMO_CONVERSATION_NOTE_PREFIX}%")
            ).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            print("Demo-client conversation fixtures already present; skipping")
            return

        demo_rows = await session.execute(
            select(DemoClient.id).order_by(DemoClient.lastname).limit(len(DEMO_CONVERSATION_FIXTURE))
        )
        demo_ids = list(demo_rows.scalars().all())
        if not demo_ids:
            print("No demo clients found; skipping conversation seed")
            return

        for i, (days_ago, channel, summary, sentiment, actions, next_steps) in enumerate(DEMO_CONVERSATION_FIXTURE):
            session.add(ClientConversation(
                id=uuid.uuid4(),
                client_id=demo_ids[i % len(demo_ids)],
                conversation_date=date.today() - timedelta(days=days_ago),
                channel=channel,
                summary=summary,
                sentiment=sentiment,
                action_items=actions,
                next_steps=next_steps,
                rm_notes=f"{DEMO_CONVERSATION_NOTE_PREFIX}: synthetic demo record",
            ))

        await session.commit()
        print(f"Seeded {len(DEMO_CONVERSATION_FIXTURE)} demo-client conversations")


# ---------------------------------------------------------------------------
# Workflow + message-artifact fixtures.
#
# GET /workflow?book_id=... is what populates the workflow selector. It reads
# workflows for FIXTURE_TENANT_001; `workflows` has a composite FK to
# client_scope, and `artifact_lineages` has a composite FK to workflows, so all
# three layers are seeded in order. No meeting / authorization records are
# fabricated — meeting_id is genuinely NULL for these messages.
# ---------------------------------------------------------------------------
WORKFLOW_FIXTURE_CREATOR = "fixture:workflow-message-seed"

# (external_id, workflow_type, status, current_stage, entry_point, days_ago)
WORKFLOW_FIXTURE = [
    ("RM001-C002", "MEETING_FOLLOWUP", "RUNNING", "DRAFT_MESSAGE", "CLIENT", 1),
    ("RM001-C003", "HOUSEHOLD_REVIEW", "NEEDS_REVIEW", "CONSOLIDATED_REVIEW", "MY_DAY", 4),
    ("RM001-C001", "OUTREACH", "COMPLETED", "READY", "PRIORITY", 9),
]

# (external_id, workflow index, mode, channel, subject, body, days_ago)
WORKFLOW_MESSAGE_FIXTURE = [
    ("RM001-C002", 0, "FOLLOWUP", "EMAIL", "Follow-up from our quarterly review",
     "Dear Mr Rahman, thank you for the quarterly review call. We confirmed that "
     "AAOIFI screening remains in force and that SGD stays as your reporting "
     "currency. A short written English summary is attached as requested.", 1),
    ("RM001-C002", 0, "FOLLOWUP", "EMAIL", "Education funding projection",
     "Dear Mr Rahman, following our discussion on funding two children's overseas "
     "education from 2031, we have prepared a projection that preserves capital "
     "in SGD. Please review before our next meeting.", 2),
    ("RM001-C003", 1, "OUTREACH", "EMAIL", "Consolidated monthly reporting pack",
     "Dear Tan Family Office, the consolidated monthly report is ready. It "
     "includes look-through exposure by legal entity and applies the agreed "
     "entity-level entitlements for the Gen-2 branches and education trusts.", 4),
    ("RM001-C001", 2, "OUTREACH", "EMAIL", "Hong Kong technology exposure note",
     "Dear Mr Wong, we have prepared the note on Hong Kong technology and fintech "
     "exposure, together with the phased rebalancing schedule we discussed to "
     "limit tax impact. Your daughter is welcome to join the next review.", 9),
]


def _message_payload(mode: str, channel: str, subject: str, body: str, external_id: str) -> str:
    """Build a valid Message artifact payload (see app.schemas.message.Message)."""
    template_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "rm-workbench:template:client-followup"))
    payload = {
        "mode": mode,
        "channel": channel,
        "template_ref": {"id": template_id, "revision": 1, "hash": "0" * 64},
        "recipients": [
            {
                "contact_id": f"{external_id}-primary",
                "destination": f"{external_id.lower()}@example.test",
                "confirmed": False,
            }
        ],
        "subject": subject,
        "body": body,
        "disclosures": [],
        "basis_refs": [],
        "priority_reason_ref": None,
        "claims": [],
    }
    return json.dumps(payload, sort_keys=True)


async def sync_workflow_message_fixtures():
    """Insert client_scope, workflows and MESSAGE artifacts for the demo.

    Idempotent: if any fixture-marked workflow already exists the whole function
    is a no-op. Insert-only — never calls clear_existing_data() and never deletes
    user-created workflows or drafts.
    """
    async with async_session_maker() as session:
        existing = await session.execute(
            select(Workflow.id).where(
                Workflow.created_by == WORKFLOW_FIXTURE_CREATOR
            ).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            print("Workflow/message fixtures already present; skipping")
            return

        client_rows = await session.execute(
            select(Client).where(Client.external_id.in_({
                row[0] for row in WORKFLOW_FIXTURE
            }))
        )
        by_external = {c.external_id: c for c in client_rows.scalars().all()}
        if not by_external:
            print("No fixture clients found; skipping workflow seed")
            return

        now = datetime.now(UTC)
        tenant = FIXTURE_TENANT_ID

        # client_scope is the FK parent of workflows. ON CONFLICT keeps this
        # safe to re-run alongside other sync functions.
        for client in by_external.values():
            await session.execute(
                text(
                    "INSERT INTO client_scope "
                    "(tenant_id, client_id, context_revision, ownership_source, "
                    " ownership_version, verified_at) "
                    "VALUES (:tenant_id, :client_id, 1, :source, :version, now()) "
                    "ON CONFLICT (tenant_id, client_id) DO NOTHING"
                ),
                {
                    "tenant_id": tenant,
                    "client_id": client.id,
                    "source": WORKFLOW_FIXTURE_CREATOR,
                    "version": "fixture-rev-001",
                },
            )

        wf_by_idx: dict[int, tuple] = {}
        for i, (external_id, wtype, wstatus, stage, entry, days_ago) in enumerate(WORKFLOW_FIXTURE):
            client = by_external.get(external_id)
            if client is None:
                continue
            wid = uuid.uuid5(
                uuid.NAMESPACE_URL, f"rm-workbench:workflow:{external_id}:{wtype}"
            )
            session.add(Workflow(
                id=wid,
                tenant_id=tenant,
                client_id=client.id,
                meeting_id=None,
                workflow_type=wtype,
                status=wstatus,
                current_stage=stage,
                row_version=1,
                context_revision=1,
                entry_point=entry,
                task_context=json.dumps({
                    "book_id": FIXTURE_BOOKS[0],
                    "source": WORKFLOW_FIXTURE_CREATOR,
                }),
                created_by=WORKFLOW_FIXTURE_CREATOR,
                created_at=now - timedelta(days=days_ago),
                updated_at=now - timedelta(days=days_ago),
            ))
            wf_by_idx[i] = (wid, tenant, client.id)
        await session.flush()

        inserted = 0
        for i, (external_id, wf_idx, mode, channel, subject, body, days_ago) in enumerate(
            WORKFLOW_MESSAGE_FIXTURE
        ):
            if wf_idx not in wf_by_idx:
                continue
            wid, wf_tenant, client_id = wf_by_idx[wf_idx]
            artifact_id = uuid.uuid5(
                uuid.NAMESPACE_URL, f"rm-workbench:message:{wid}:{i}"
            )
            revision_id = uuid.uuid5(
                uuid.NAMESPACE_URL, f"rm-workbench:message-revision:{artifact_id}:1"
            )
            raw = _message_payload(mode, channel, subject, body, external_id)
            session.add(ArtifactLineage(
                id=artifact_id,
                tenant_id=wf_tenant,
                client_id=client_id,
                workflow_id=wid,
                meeting_id=None,
                kind="MESSAGE",
                current_revision_id=revision_id,
                created_by=WORKFLOW_FIXTURE_CREATOR,
                created_at=now - timedelta(days=days_ago),
            ))
            await session.flush()
            session.add(ArtifactRevision(
                id=revision_id,
                tenant_id=wf_tenant,
                client_id=client_id,
                artifact_id=artifact_id,
                version=1,
                content_hash=hashlib.sha256(raw.encode()).hexdigest(),
                payload=raw,
                environment_kind="FIXTURE",
                environment_id=FIXTURE_ENVIRONMENT_ID,
                created_by=WORKFLOW_FIXTURE_CREATOR,
                created_at=now - timedelta(days=days_ago),
            ))
            inserted += 1

        await session.commit()
        print(f"Seeded {len(wf_by_idx)} workflows and {inserted} message artifacts")


async def _clients_exist() -> bool:
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT 1 FROM clients LIMIT 1"))
        return result.first() is not None


async def main():
    """Main seed function"""
    import os

    print("🌱 Starting database seed...")

    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required to seed demo data")

    force = os.getenv("FORCE_SEED", "").strip().lower() in {"1", "true", "yes"}

    try:
        # Identity/reference rows first: the destructive client seed below and all
        # FK-constrained runtime writes depend on them.
        await seed_fixture_environment()
        if not force and await _clients_exist():
            print("ℹ️  Demo clients already present — skipping destructive re-seed.")
            print("   Set FORCE_SEED=true to wipe and re-seed.")
            return
        await clear_existing_data()
        await seed_clients()
        await seed_holdings()
        await seed_interactions()
        print("✅ Database seeding complete!")
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
