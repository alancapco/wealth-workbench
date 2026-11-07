"""
Client Memory Service - Persistent relationship context
Implements D5 memory requirements (G-13)
"""
from typing import Dict, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, select
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
import logging

logger = logging.getLogger(__name__)

class ClientMemory(Base):
    """Persistent client memory and relationship graph"""
    __tablename__ = "client_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    memory_type = Column(String, nullable=False)  # preference, relationship, context
    key = Column(String, nullable=False)
    value = Column(Text)
    metadata = Column(JSON, default=dict)
    confidence = Column(String)  # low, medium, high
    source = Column(String)  # interaction, crm, inferred
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class MemoryService:
    async def store_memory(
        self,
        db: AsyncSession,
        client_id: str,
        memory_type: str,
        key: str,
        value: str,
        metadata: Dict = None,
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
                metadata=metadata or {},
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
                    "metadata": m.metadata,
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
