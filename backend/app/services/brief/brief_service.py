"""
Brief Service - Generate meeting briefs from real data
Implements versioning and provenance tracking
"""
from typing import Dict, Optional
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.models import Client, Interaction, Holding
from app.services.market.market_service import market_data_service
import logging
import uuid

logger = logging.getLogger(__name__)

MATERIAL_MOVE_THRESHOLD = 2.0


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
        - Market News: from Newsfilter / Yahoo Finance (English)
        - Proposed Agenda: derived from structured movements and context
        """
        brief_id = str(uuid.uuid4())
        generated_at = datetime.now(timezone.utc)

        try:
            # client_id arrives as a string from the API; the UUID column needs a real UUID.
            client_uuid = client_id if isinstance(client_id, UUID) else UUID(str(client_id))
            result = await db.execute(
                select(Client).where(Client.id == client_uuid)
            )
            client = result.scalar_one_or_none()

            if not client:
                raise ValueError(f"Client {client_id} not found")

            portfolio_section = await self._build_portfolio_overview(client, db)
            changes_section, movements = await self._build_material_changes(client, db)
            interactions_section = await self._build_recent_interactions(client, db)
            news_section = await self._build_market_news(client, db)
            agenda_section = await self._build_proposed_agenda(client, movements)

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

    @staticmethod
    def _section(content: str, source: str, source_kind: str, confidence: float) -> Dict:
        """Wrap section text with its provenance."""
        return {
            "content": content,
            "provenance": {
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence": confidence,
                "source_kind": source_kind
            }
        }

    async def _build_portfolio_overview(self, client: Client, db: AsyncSession) -> Dict:
        """Build portfolio overview from holdings table"""
        result = await db.execute(
            select(Holding).where(Holding.client_id == client.id)
        )
        holdings = result.scalars().all()

        currency = client.currency or "USD"
        total_value = sum(h.current_value or 0 for h in holdings)
        content_lines = [
            f"Client: {client.name}",
            f"Total AUM: {currency} {client.aum or 0:,.0f}",
            f"Risk Profile: {client.risk_profile or 'not recorded'}",
            f"Recorded holdings value: {currency} {total_value:,.0f}",
            "",
            "Holdings:"
        ]

        for holding in holdings:
            content_lines.append(
                f"  • {holding.symbol}: {holding.quantity or 0:g} units @ {currency} {holding.current_value or 0:,.0f}"
            )
        if not holdings:
            content_lines.append("  No holdings recorded for this client.")

        return self._section("\n".join(content_lines), "Holdings Database", "database", 1.0)

    async def _build_material_changes(self, client: Client, db: AsyncSession):
        """Build material changes from structured quote data.

        The market service's no-key fallback is synthetic, so quotes are only
        consumed when a real quote provider key is configured.
        """
        result = await db.execute(
            select(Holding).where(Holding.client_id == client.id)
        )
        holdings = result.scalars().all()
        symbols = [h.symbol for h in holdings if h.symbol]

        if not symbols or not (settings.ALPHAVANTAGE_API_KEY or "").strip():
            return (
                self._section(
                    "Live price moves are unavailable: no holdings or no quote provider configured.",
                    "quote provider unconfigured", "UNCONFIGURED", 0.0
                ),
                []
            )

        quotes = await market_data_service.get_real_time_quote(symbols)
        by_symbol = {quote["symbol"]: quote for quote in quotes}
        currency = client.currency or "USD"
        source = "AlphaVantage"
        changes = []
        movements = []
        for holding in holdings:
            quote = by_symbol.get(holding.symbol)
            if not quote:
                changes.append(f"{holding.symbol}: no quote returned")
                continue
            source = quote.get("source_id") or source
            pct = float(quote["change_percent"])
            impact = (holding.current_value or 0) * abs(pct) / 100
            material = abs(pct) >= MATERIAL_MOVE_THRESHOLD
            quoted_as = quote.get("quoted_symbol")
            via = f" (quoted as {quoted_as})" if quoted_as and quoted_as != holding.symbol else ""
            movements.append({
                "symbol": holding.symbol,
                "change_percent": pct,
                "price": float(quote["price"]),
                "impact": impact,
                "material": material,
            })
            changes.append(
                f"{holding.symbol}{via} {pct:+.2f}% at {float(quote['price']):.2f}. "
                f"Position impact {currency} {impact:,.0f}."
                + (" Material move." if material else " Within the 2% material threshold.")
            )

        content = "\n".join(changes) if changes else "No quotes returned by the configured provider."
        if not movements:
            return self._section(content, source, "UNAVAILABLE", 0.0), []
        return self._section(content, source, "LIVE_FEED", 1.0), movements

    async def _build_recent_interactions(self, client: Client, db: AsyncSession) -> Dict:
        """Build recent interactions from database"""
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
        return self._section(content, "CRM & D5 Memory", "database", 0.92)

    async def _build_market_news(self, client: Client, db: AsyncSession) -> Dict:
        """News for the client's holdings, then the general market feed."""
        result = await db.execute(
            select(Holding.symbol).where(Holding.client_id == client.id)
        )
        symbols = [row[0] for row in result.all() if row[0]]
        if not market_data_service.news_configured:
            return self._section(
                "No market news available from the configured provider.",
                "none", "UNCONFIGURED", 0.0
            )
        try:
            news_items, source_label, _ = await market_data_service.get_market_news(
                symbols=symbols or None, limit=4
            )
            if not news_items:
                news_items, source_label, _ = await market_data_service.get_market_news(limit=4)

            content_lines = []
            source = None
            for item in news_items:
                source = item.get("source") or source
                summary = (item.get("content") or "").strip()
                line = f"• {item.get('title') or 'Untitled'}"
                if summary:
                    line += f": {summary[:240]}"
                content_lines.append(line)

            if not content_lines:
                return self._section(
                    "No market news available from the configured provider.",
                    source_label or "none", "UNAVAILABLE", 0.0
                )
            return self._section("\n".join(content_lines), source or source_label, "LIVE_FEED", 1.0)
        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            return self._section("Market news request failed.", "none", "UNAVAILABLE", 0.0)

    async def _build_proposed_agenda(self, client: Client, movements: list[Dict]) -> Dict:
        """Derive agenda items from structured market movements, not text matching."""
        agenda_items = []
        material = [m for m in movements if m["material"]]
        if material:
            symbols = ", ".join(dict.fromkeys(m["symbol"] for m in material))
            largest = max(material, key=lambda m: abs(m["change_percent"]))
            agenda_items.append(
                f"1. Review material price moves in {symbols} "
                f"(largest: {largest['symbol']} {largest['change_percent']:+.2f}%) and the position impact"
            )

        if client.preferences and "last_rebalancing" in client.preferences:
            agenda_items.append(f"{len(agenda_items) + 1}. Discuss rebalancing approach")

        agenda_items.extend([
            f"{len(agenda_items) + 1}. Review overall portfolio performance",
            f"{len(agenda_items) + 2}. Q&A and next steps"
        ])

        return self._section("\n".join(agenda_items), "Derived from recorded context", "ai_generated", 0.85)

brief_service = BriefService()
