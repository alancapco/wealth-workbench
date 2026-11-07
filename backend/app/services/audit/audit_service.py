"""
Audit Service - Track all actions for compliance
"""
from typing import Dict
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog
import uuid
import logging

logger = logging.getLogger(__name__)

class AuditService:
    async def log_action(
        self,
        db: AsyncSession,
        action_type: str,
        entity_type: str,
        entity_id: str,
        actor: str,
        details: Dict = None
    ):
        """
        Log an action to the audit trail
        """
        try:
            audit_log = AuditLog(
                id=uuid.uuid4(),
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                actor=actor,
                details=details or {},
                timestamp=datetime.now(timezone.utc)
            )

            db.add(audit_log)
            await db.commit()

            logger.info(f"Audit log created: {action_type} on {entity_type}/{entity_id} by {actor}")

        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            await db.rollback()
            raise

audit_service = AuditService()
