"""Base repository pattern with tenant scope enforcement."""
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class TenantScopedRepository(Generic[T]):
    """Base repository enforcing tenant isolation for all queries."""

    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class

    def _tenant_filter(self, tenant_id: str, query):
        """Apply tenant_id filter to query."""
        return query.where(self.model_class.tenant_id == tenant_id)

    async def get_by_id(self, tenant_id: str, entity_id: UUID) -> T | None:
        """Retrieve entity by ID within tenant scope."""
        stmt = select(self.model_class).where(
            self.model_class.tenant_id == tenant_id,
            self.model_class.id == entity_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[T]:
        """List entities within tenant scope with pagination."""
        stmt = (
            select(self.model_class)
            .where(self.model_class.tenant_id == tenant_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ClientScopedRepository(Generic[T]):
    """Base repository enforcing tenant + client composite scope."""

    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, tenant_id: str, client_id: UUID, entity_id: UUID) -> T | None:
        """Retrieve entity by ID within tenant + client scope."""
        stmt = select(self.model_class).where(
            self.model_class.tenant_id == tenant_id,
            self.model_class.client_id == client_id,
            self.model_class.id == entity_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_client(
        self, tenant_id: str, client_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[T]:
        """List entities within tenant + client scope."""
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.tenant_id == tenant_id,
                self.model_class.client_id == client_id
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
