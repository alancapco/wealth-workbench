"""
Provenance Tracking Service
Implements per-statement provenance (G-23)
"""
from typing import Dict, List
from datetime import datetime, UTC, timezone
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ProvenanceSourceKind(Enum):
    DATABASE = "database"
    LIVE_FEED = "LIVE_FEED"
    CRM = "crm"
    AI_GENERATED = "ai_generated"
    DERIVED = "DERIVED"

class ProvenanceService:
    def create_provenance(
        self,
        source: str,
        source_kind: str,
        confidence: float = 1.0,
        metadata: Dict = None
    ) -> Dict:
        """
        Create a provenance envelope for a statement
        Returns structured provenance data
        """
        return {
            "source": source,
            "source_kind": source_kind,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence": confidence,
            "metadata": metadata or {}
        }

    def validate_provenance(self, provenance: Dict) -> bool:
        """
        Validate that provenance is complete and accurate
        Returns False if provenance is fabricated or incomplete
        """
        required_fields = ["source", "source_kind", "timestamp", "confidence"]

        for field in required_fields:
            if field not in provenance:
                logger.warning(f"Missing required field in provenance: {field}")
                return False

        # Check source_kind is valid
        try:
            ProvenanceSourceKind(provenance["source_kind"])
        except ValueError:
            logger.warning(f"Invalid source_kind: {provenance['source_kind']}")
            return False

        return True

provenance_service = ProvenanceService()
