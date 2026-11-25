"""
Client Ranking Service
Implements the prioritization algorithm based on Opportunity, Risk, and Retention
"""
from typing import List, Dict
from datetime import datetime, UTC, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Client, Holding, Interaction
from app.services.ranking.policy_config import get_concentration_threshold
import logging

logger = logging.getLogger(__name__)

class RankingService:
    def __init__(self):
        self.weights = {
            "opportunity": 0.4,
            "risk": 0.35,
            "retention": 0.25
        }

    async def rank_clients(
        self,
        db: AsyncSession,
        rm_id: str,
        market_signals: List[Dict] = None
    ) -> List[Dict]:
        """
        Rank clients based on Opportunity, Risk, and Retention scores
        Returns prioritized client list with reason codes
        """
        try:
            # Get all clients for this RM
            result = await db.execute(
                select(Client).where(Client.external_id.like(f"{rm_id}%"))
            )
            clients = result.scalars().all()

            # Threshold is a policy input, resolved once per run from the config service.
            tenant_id = next((c.tenant_id for c in clients if c.tenant_id), None)
            concentration_threshold = await get_concentration_threshold(db, tenant_id)

            ranked_clients = []

            for client in clients:
                # Calculate scores
                opportunity_score = await self._calculate_opportunity(client, market_signals, db)
                risk_score = await self._calculate_risk(client, db, concentration_threshold)
                retention_score = await self._calculate_retention(client, db)

                # Weighted total score
                total_score = (
                    opportunity_score * self.weights["opportunity"] +
                    risk_score * self.weights["risk"] +
                    retention_score * self.weights["retention"]
                )

                # Generate reason code
                reason = self._generate_reason_code(
                    opportunity_score, risk_score, retention_score, market_signals
                )

                ranked_clients.append({
                    "client_id": str(client.id),
                    "name": client.name,
                    "aum": client.aum,
                    "total_score": total_score,
                    "opportunity_score": opportunity_score,
                    "risk_score": risk_score,
                    "retention_score": retention_score,
                    "reason": reason,
                    "evidence": self._gather_evidence(client, market_signals)
                })

            # Sort by total score descending
            ranked_clients.sort(key=lambda x: x["total_score"], reverse=True)

            # Add rank positions
            for idx, client in enumerate(ranked_clients, 1):
                client["rank"] = idx

            logger.info(f"Ranked {len(ranked_clients)} clients for RM {rm_id}")
            return ranked_clients

        except Exception as e:
            logger.error(f"Error ranking clients: {e}")
            return []

    async def _calculate_opportunity(
        self,
        client: Client,
        market_signals: List[Dict],
        db: AsyncSession
    ) -> float:
        """
        Calculate opportunity score based on:
        - Portfolio drift from market movements
        - Rebalancing opportunities
        - Product fit
        """
        score = 0.0

        # Check portfolio drift from market signals
        if market_signals:
            # Get client holdings
            result = await db.execute(
                select(Holding).where(Holding.client_id == client.id)
            )
            holdings = result.scalars().all()

            for signal in market_signals:
                for holding in holdings:
                    if holding.symbol == signal["symbol"]:
                        # Significant movement in client's holding
                        score += min(abs(signal["change_percent"]) / 10, 5.0)

        # Check time since last rebalancing (from preferences)
        if client.preferences and "last_rebalancing" in client.preferences:
            try:
                last_rebal_str = client.preferences["last_rebalancing"]
                last_rebal = datetime.fromisoformat(last_rebal_str)
                # Make timezone-aware if naive
                if last_rebal.tzinfo is None:
                    last_rebal = last_rebal.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_since = (now - last_rebal).days
                if days_since > 90:
                    score += 2.0
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid last_rebalancing date for client {client.id}: {e}")

        return min(score, 10.0)

    async def _calculate_risk(
        self,
        client: Client,
        db: AsyncSession,
        concentration_threshold: float,
    ) -> float:
        """
        Calculate risk score based on:
        - Portfolio concentration
        - Volatility exposure
        - Suitability expiry
        """
        score = 0.0

        # Check suitability expiry
        if client.preferences and "suitability_expiry" in client.preferences:
            try:
                expiry_str = client.preferences["suitability_expiry"]
                expiry = datetime.fromisoformat(expiry_str)
                # Make timezone-aware if naive
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_until_expiry = (expiry - now).days

                if days_until_expiry < 0:
                    score += 8.0  # Expired
                elif days_until_expiry < 30:
                    score += 5.0  # Expiring soon
                elif days_until_expiry < 60:
                    score += 3.0
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid suitability_expiry for client {client.id}: {e}")

        result = await db.execute(
            select(Holding).where(Holding.client_id == client.id)
        )
        holdings = result.scalars().all()
        if holdings:
            total_value = sum(h.current_value or 0 for h in holdings)
            if total_value > 0:
                for holding in holdings:
                    concentration = (holding.current_value or 0) / total_value
                    if concentration > concentration_threshold:
                        score += 2.0

        return min(score, 10.0)

    async def _calculate_retention(self, client: Client, db: AsyncSession) -> float:
        """
        Calculate retention score based on:
        - Last interaction date
        - Communication frequency
        - Client satisfaction signals
        """
        score = 0.0

        # Get recent interactions
        result = await db.execute(
            select(Interaction)
            .where(Interaction.client_id == client.id)
            .order_by(Interaction.interaction_date.desc())
            .limit(10)
        )
        interactions = result.scalars().all()

        if interactions:
            # Time since last interaction
            last_interaction = interactions[0].interaction_date
            # Make timezone-aware if naive
            if last_interaction.tzinfo is None:
                last_interaction = last_interaction.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days_since = (now - last_interaction).days

            if days_since > 90:
                score += 5.0
            elif days_since > 60:
                score += 3.0
            elif days_since > 30:
                score += 1.0

            # Interaction frequency (interactions in last 6 months)
            six_months_ago = now - timedelta(days=180)
            recent_interactions = [
                i for i in interactions
                if (i.interaction_date.replace(tzinfo=timezone.utc) if i.interaction_date.tzinfo is None else i.interaction_date) > six_months_ago
            ]

            if len(recent_interactions) < 2:
                score += 3.0
        else:
            # No interactions recorded
            score += 8.0

        return min(score, 10.0)

    def _generate_reason_code(
        self,
        opp_score: float,
        risk_score: float,
        ret_score: float,
        market_signals: List[Dict]
    ) -> Dict:
        """
        Generate human-readable reason code
        """
        # Determine primary reason
        scores = {
            "OPPORTUNITY": opp_score,
            "RISK": risk_score,
            "RETENTION": ret_score
        }
        primary_reason = max(scores, key=scores.get)

        descriptions = {
            "OPPORTUNITY": "Portfolio drift triggered by market event",
            "RISK": "Suitability review required or concentration risk",
            "RETENTION": "Client engagement attention needed"
        }

        return {
            "code": primary_reason,
            "description": descriptions[primary_reason],
            "score": scores[primary_reason]
        }

    def _gather_evidence(self, client: Client, market_signals: List[Dict]) -> List[Dict]:
        """
        Gather evidence chips for ranking decision
        """
        evidence = []

        if market_signals:
            for signal in market_signals:
                evidence.append({
                    "type": "LIVE_FEED",
                    "source": signal.get("source") or "AlphaVantage",
                    "timestamp": signal.get("timestamp"),
                    "description": f"{signal['symbol']} {signal['change_percent']:+.2f}%"
                })

        evidence.append({
            "type": "DERIVED",
            "source": "rank.clients v1.2",
            "timestamp": datetime.now(),
            "description": "Ranking algorithm"
        })

        return evidence

# Singleton instance
ranking_service = RankingService()
