"""
Client Memory Service - Persistent relationship context
Implements D5 memory requirements (G-13)
"""
from typing import Dict, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.memory import ClientMemory
import uuid
import logging

logger = logging.getLogger(__name__)


class MemoryService:
    async def store_memory(
        self,
        db: AsyncSession,
        client_id: str,
        memory_type: str,
        key: str,
        value: str,
        extra_metadata: Dict = None,
        confidence: str = "medium",
        source: str = "interaction"
    ):
        """Store a memory item for a client"""
        try:
            memory = ClientMemory(
                client_id=uuid.UUID(client_id),
                memory_type=memory_type,
                key=key,
                value=value,
                extra_metadata=extra_metadata or {},
                confidence=confidence,
                source=source,
                created_at=datetime.now(timezone.utc)
            )

            db.add(memory)
            await db.commit()

            logger.info(f"Stored memory {key} for client {client_id}")

        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            await db.rollback()
            raise

    async def get_memories(
        self,
        db: AsyncSession,
        client_id: str,
        memory_type: str = None
    ) -> List[Dict]:
        """Retrieve memories for a client"""
        try:
            query = select(ClientMemory).where(
                ClientMemory.client_id == uuid.UUID(client_id)
            )

            if memory_type:
                query = query.where(ClientMemory.memory_type == memory_type)

            result = await db.execute(query.order_by(ClientMemory.created_at.desc()))
            memories = result.scalars().all()

            return [
                {
                    "id": str(m.id),
                    "memory_type": m.memory_type,
                    "key": m.key,
                    "value": m.value,
                    "extra_metadata": m.extra_metadata,
                    "confidence": m.confidence,
                    "source": m.source,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in memories
            ]

        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []

memory_service = MemoryService()
