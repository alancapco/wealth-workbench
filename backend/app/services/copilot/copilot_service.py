"""
Copilot Orchestration Service
Implements the workflow orchestration and AI-powered brief generation
Uses OpenAI-compatible API (works with OpenAI, Anthropic, or any compatible endpoint)
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.models import WorkflowStage, SourceKind
import logging
import json

logger = logging.getLogger(__name__)

class CopilotService:
    def __init__(self):
        # Initialize OpenAI-compatible client with configurable base URL
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        self.model = settings.LLM_MODEL
        logger.info(f"Copilot initialized with model: {self.model} at {settings.LLM_BASE_URL}")

    async def generate_brief(
        self,
        client_data: Dict,
        portfolio_data: List[Dict],
        market_signals: List[Dict],
        interaction_history: List[Dict]
    ) -> Dict:
        """
        Generate five-section client brief with provenance
        """
        try:
            correlation_id = uuid.uuid4()

            # Build context for AI
            context = self._build_context(
                client_data, portfolio_data, market_signals, interaction_history
            )

            # Generate brief sections using AI
            brief = await self._generate_with_ai(context)

            # Add provenance to each section
            brief["portfolio_overview"]["provenance"] = {
                "source_kind": SourceKind.DERIVED.value,
                "source": "Copilot Brief Generator",
                "version": "v1.2",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": str(correlation_id)
            }

            brief["material_changes"]["provenance"] = {
                "source_kind": SourceKind.LIVE_FEED.value,
                "source": "TigerBroker + Copilot",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": str(correlation_id)
            }

            brief["recent_interactions"]["provenance"] = {
                "source_kind": SourceKind.RM_MANUAL.value,
                "source": "D5 Client Memory",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": str(correlation_id)
            }

            brief["market_news"]["provenance"] = {
                "source_kind": SourceKind.LIVE_FEED.value,
                "source": "TigerBroker News",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": str(correlation_id)
            }

            brief["proposed_agenda"]["provenance"] = {
                "source_kind": SourceKind.DERIVED.value,
                "source": "Copilot Brief Generator",
                "version": "v1.2",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": str(correlation_id)
            }

            logger.info(f"Generated brief with correlation_id {correlation_id}")
            return brief

        except Exception as e:
            logger.error(f"Error generating brief: {e}")
            return self._generate_fallback_brief()

    def _build_context(
        self,
        client_data: Dict,
        portfolio_data: List[Dict],
        market_signals: List[Dict],
        interaction_history: List[Dict]
    ) -> str:
        """Build context string for AI prompt"""
        context = f"""
Client Profile:
- Name: {client_data.get('name')}
- AUM: {client_data.get('aum')} {client_data.get('currency', 'USD')}
- Risk Profile: {client_data.get('risk_profile', 'Moderate')}
- Preferences: {json.dumps(client_data.get('preferences', {}))}

Current Portfolio:
"""
        for holding in portfolio_data:
            context += f"- {holding['symbol']}: {holding['quantity']} shares, value: {holding['current_value']}\n"

        context += "\nMarket Signals:\n"
        for signal in market_signals:
            context += f"- {signal['symbol']}: {signal['change_percent']:+.2f}%\n"

        context += "\nRecent Interactions:\n"
        for interaction in interaction_history[-3:]:
            context += f"- {interaction.get('interaction_date')}: {interaction.get('summary')}\n"

        return context

    async def _generate_with_ai(self, context: str) -> Dict:
        """Use AI to generate brief content via OpenAI-compatible API"""
        try:
            prompt = f"""You are a wealth management AI assistant. Generate a concise 5-section client brief based on the following context.

{context}

Generate a JSON response with these sections:
1. portfolio_overview: Current allocation and key metrics
2. material_changes: Recent portfolio changes and market impacts
3. recent_interactions: Summary of last 3 interactions
4. market_news: Relevant market news affecting this client
5. proposed_agenda: Meeting agenda items (3-5 bullets)

Format as JSON with keys: portfolio_overview, material_changes, recent_interactions, market_news, proposed_agenda.
Each section should have 'content' as a string."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional wealth management assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            brief = json.loads(response.choices[0].message.content)
            return brief

        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return self._generate_fallback_brief()

    def _generate_fallback_brief(self) -> Dict:
        """Fallback brief when AI fails"""
        return {
            "portfolio_overview": {
                "content": "Portfolio data temporarily unavailable. Please review manually."
            },
            "material_changes": {
                "content": "No significant changes detected."
            },
            "recent_interactions": {
                "content": "Interaction history available in client record."
            },
            "market_news": {
                "content": "Market news feed temporarily unavailable."
            },
            "proposed_agenda": {
                "content": "1. Review portfolio performance\n2. Discuss investment objectives\n3. Address any client questions"
            }
        }

    async def orchestrate_workflow(
        self,
        workflow_type: str,
        client_id: str,
        trigger: Dict
    ) -> Dict:
        """
        Orchestrate complete workflow from trigger to completion
        """
        correlation_id = uuid.uuid4()
        workflow_instance = {
            "correlation_id": str(correlation_id),
            "workflow_type": workflow_type,
            "client_id": client_id,
            "trigger": trigger,
            "stages": [],
            "current_stage": WorkflowStage.RANK_CLIENTS.value,
            "status": "in_progress",
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"Starting workflow {workflow_type} with correlation_id {correlation_id}")
        return workflow_instance

    async def extract_meeting_insights(
        self,
        transcript: str,
        client_context: Dict
    ) -> Dict:
        """
        Extract preferences, action items, and insights from meeting transcript
        Uses OpenAI-compatible API
        """
        try:
            prompt = f"""Analyze this meeting transcript and extract:
1. Client preferences mentioned
2. Action items and commitments
3. Family/relationship updates
4. Investment preferences or concerns

Client: {client_context.get('name')}
Transcript: {transcript}

Return JSON with: preferences (list), action_items (list), family_updates (list), concerns (list)"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a meeting analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            insights = json.loads(response.choices[0].message.content)
            insights["provenance"] = {
                "source_kind": SourceKind.DERIVED.value,
                "source": f"Copilot Meeting Analyzer ({self.model})",
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat()
            }

            return insights

        except Exception as e:
            logger.error(f"Error extracting meeting insights: {e}")
            return {"error": str(e)}

# Singleton instance
copilot_service = CopilotService()
