"""
Brief Service - Generate meeting briefs from real data
Implements versioning and provenance tracking
"""
from typing import Dict, Optional, List
from datetime import datetime, UTC, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Client, Interaction, Holding
from app.services.market.market_service import market_data_service
import logging
import uuid

logger = logging.getLogger(__name__)

class BriefService:
    async def generate_brief(
        self,
        client_id: str,
        db: AsyncSession,
        version: Optional[int] = None
    ) -> Dict:
        """
        Generate a 5-section meeting brief from real data sources
        - Portfolio Overview: from holdings table
        - Material Changes: from live market data
        - Recent Interactions: from interactions table
        - Market News: from TigerBroker
        - Proposed Agenda: AI-generated from above context
        """
        brief_id = str(uuid.uuid4())
        generated_at = datetime.now(timezone.utc)

        try:
            # Get client from database
            result = await db.execute(
                select(Client).where(Client.id == client_id)
            )
            client = result.scalar_one_or_none()

            if not client:
                raise ValueError(f"Client {client_id} not found")

            # Section 1: Portfolio Overview
            portfolio_section = await self._build_portfolio_overview(client, db)

            # Section 2: Material Changes
            changes_section = await self._build_material_changes(client, db)

            # Section 3: Recent Interactions
            interactions_section = await self._build_recent_interactions(client, db)

            # Section 4: Market News
            news_section = await self._build_market_news(client, db)

            # Section 5: Proposed Agenda
            agenda_section = await self._build_proposed_agenda(
                client, portfolio_section, changes_section, interactions_section
            )

            brief = {
                "brief_id": brief_id,
                "client_id": client_id,
                "client_name": client.name,
                "version": version or 1,
                "generated_at": generated_at.isoformat(),
                "sections": {
                    "portfolio_overview": portfolio_section,
                    "material_changes": changes_section,
                    "recent_interactions": interactions_section,
                    "market_news": news_section,
                    "proposed_agenda": agenda_section
                }
            }

            logger.info(f"Generated brief {brief_id} for client {client_id}")
            return brief

        except Exception as e:
            logger.error(f"Error generating brief for client {client_id}: {e}")
            raise

    async def _build_portfolio_overview(self, client: Client, db: AsyncSession) -> Dict:
        """Build portfolio overview from holdings table"""
        result = await db.execute(
            select(Holding).where(Holding.client_id == client.id)
        )
        holdings = result.scalars().all()

        total_value = sum(h.current_value or 0 for h in holdings)

        # Build content from real data
        content_lines = [
            f"Client: {client.name}",
            f"Total AUM: {client.currency} {client.aum:,.0f}",
            f"Risk Profile: {client.risk_profile}",
            f"",
            "Holdings:"
        ]

        for holding in holdings:
            content_lines.append(
                f"  • {holding.symbol}: {holding.quantity} units @ {client.currency} {holding.current_value:,.0f}"
            )

        return {
            "content": "\n".join(content_lines),
            "provenance": {
                "source": "Holdings Database",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence": 1.0,
                "source_kind": "database"
            }
        }

    async def _build_material_changes(self, client: Client, db: AsyncSession) -> Dict:
        """Build material changes from live market data"""
        result = await db.execute(
            select(Holding).where(Holding.client_id == client.id)
        )
        holdings = result.scalars().all()

        symbols = [holding.symbol for holding in holdings]
        quotes = await market_data_service.get_real_time_quote(symbols) if symbols else []
        by_symbol = {quote["symbol"]: quote for quote in quotes}

        changes = []
        source = "Alpha Vantage"
        for holding in holdings:
            quote = by_symbol.get(holding.symbol)
            if not quote:
                changes.append(f"{holding.symbol}: no quote returned")
                continue
            source = quote.get("source_id") or source
            quoted_as = quote.get("quoted_symbol")
            via = f" (quoted as {quoted_as})" if quoted_as and quoted_as != holding.symbol else ""
            impact = (holding.current_value or 0) * abs(quote["change_percent"]) / 100
            material = abs(quote["change_percent"]) >= 2
            changes.append(
                f"{holding.symbol}{via} {quote['change_percent']:+.2f}% at {quote['price']:.2f}. "
                f"Position impact {client.currency} {impact:,.0f}."
                + (" Material move." if material else " Within the 2% material threshold.")
            )

        content = "\n".join(changes) if changes else "No holdings to compare with market prices."

        return {
            "content": content,
            "provenance": {
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence": 1.0,
                "source_kind": "LIVE_FEED"
            }
        }

    async def _build_recent_interactions(self, client: Client, db: AsyncSession) -> Dict:
        """Build recent interactions from database"""
        # Get interactions from database
        result = await db.execute(
            select(Interaction)
            .where(Interaction.client_id == client.id)
            .order_by(Interaction.interaction_date.desc())
            .limit(5)
        )
        interactions = result.scalars().all()

        content_lines = []
        now = datetime.now(timezone.utc)
        for interaction in interactions:
            when = interaction.interaction_date
            if when is None:
                days_ago = None
            else:
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                days_ago = (now - when).days
            when_label = "undated" if days_ago is None else f"{days_ago} days ago"
            kind = (interaction.interaction_type or "interaction").replace("_", " ").title()
            content_lines.append(f"• {kind} ({when_label}): {interaction.summary or 'No summary recorded.'}")

        content = "\n".join(content_lines) if content_lines else "No recent interactions recorded."

        return {
            "content": content,
            "provenance": {
                "source": "CRM & D5 Memory",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence": 0.92,
                "source_kind": "database"
            }
        }

    async def _build_market_news(self, client: Client, db: AsyncSession) -> Dict:
        """News for the client's holdings, then the general market feed."""
        result = await db.execute(
            select(Holding.symbol).where(Holding.client_id == client.id)
        )
        symbols = [row[0] for row in result.all() if row[0]]
        source = "Tiger Broker"
        try:
            news_items = []
            if symbols:
                news_items = await market_data_service.get_market_news(symbols=symbols, limit=4)
            if not news_items:
                news_items = await market_data_service.get_market_news(limit=4)
            content_lines = []
            for item in news_items:
                source = item.get("source") or source
                summary = (item.get("content") or "").strip()
                line = f"• {item.get('title') or 'Untitled'}"
                if summary:
                    line += f": {summary[:240]}"
                content_lines.append(line)
            content = "\n".join(content_lines) if content_lines else "No market news returned for this client."
        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            content = "Market news request failed."

        return {
            "content": content,
            "provenance": {
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence": 1.0,
                "source_kind": "LIVE_FEED"
            }
        }

    async def _build_proposed_agenda(
        self,
        client: Client,
        portfolio: Dict,
        changes: Dict,
        interactions: Dict
    ) -> Dict:
        """Build proposed agenda based on context"""
        agenda_items = []

        # Add agenda items based on material changes
        if "%" in changes["content"]:
            agenda_items.append("1. Review today's price moves and the position impact")

        # Add rebalancing if needed
        if client.preferences and "last_rebalancing" in client.preferences:
            agenda_items.append("2. Discuss rebalancing approach")

        # Default items
        agenda_items.extend([
            f"{len(agenda_items) + 1}. Review overall portfolio performance",
            f"{len(agenda_items) + 2}. Q&A and next steps"
        ])

        content = "\n".join(agenda_items)

        return {
            "content": content,
            "provenance": {
                "source": "AI Generated",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence": 0.85,
                "source_kind": "ai_generated"
            }
        }

brief_service = BriefService()
