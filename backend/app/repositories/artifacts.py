"""Artifact lineage and revision repositories."""
from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ArtifactLineage, ArtifactRevision, ArtifactItem, ReviewDecision
from app.repositories.base import ClientScopedRepository


class ArtifactRepository(ClientScopedRepository[ArtifactLineage]):
    """Repository for artifact lineage operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ArtifactLineage)

    async def create_lineage(
        self,
        tenant_id: str,
        client_id: UUID,
        workflow_id: UUID,
        kind: str,
        created_by: str,
        meeting_id: UUID | None = None,
    ) -> ArtifactLineage:
        """Create new artifact lineage."""
        lineage = ArtifactLineage(
            tenant_id=tenant_id,
            client_id=client_id,
            workflow_id=workflow_id,
            meeting_id=meeting_id,
            kind=kind,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        self.session.add(lineage)
        await self.session.flush()
        return lineage

    async def get_by_kind(
        self, tenant_id: str, client_id: UUID, kind: str, limit: int = 10
    ) -> list[ArtifactLineage]:
        """Get artifact lineages by kind, newest first."""
        stmt = (
            select(ArtifactLineage)
            .where(
                ArtifactLineage.tenant_id == tenant_id,
                ArtifactLineage.client_id == client_id,
                ArtifactLineage.kind == kind,
            )
            .order_by(desc(ArtifactLineage.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class RevisionRepository(ClientScopedRepository[ArtifactRevision]):
    """Repository for artifact revision operations with immutability enforcement."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ArtifactRevision)

    async def create_revision(
        self,
        tenant_id: str,
        client_id: UUID,
        artifact_id: UUID,
        version: int,
        content_hash: str,
        payload: str,
        environment_kind: str,
        environment_id: str,
        created_by: str,
    ) -> ArtifactRevision:
        """Create immutable artifact revision."""
        revision = ArtifactRevision(
            tenant_id=tenant_id,
            client_id=client_id,
            artifact_id=artifact_id,
            version=version,
            content_hash=content_hash,
            payload=payload,
            environment_kind=environment_kind,
            environment_id=environment_id,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        self.session.add(revision)
        await self.session.flush()
        return revision

    async def get_by_version(
        self, tenant_id: str, artifact_id: UUID, version: int
    ) -> ArtifactRevision | None:
        """Get specific version of artifact by tenant + artifact_id + version unique key."""
        stmt = select(ArtifactRevision).where(
            ArtifactRevision.tenant_id == tenant_id,
            ArtifactRevision.artifact_id == artifact_id,
            ArtifactRevision.version == version,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_current_revision(
        self, tenant_id: str, client_id: UUID, artifact_id: UUID
    ) -> ArtifactRevision | None:
        """Get the highest version number for this artifact."""
        stmt = (
            select(ArtifactRevision)
            .where(
                ArtifactRevision.tenant_id == tenant_id,
                ArtifactRevision.client_id == client_id,
                ArtifactRevision.artifact_id == artifact_id,
            )
            .order_by(desc(ArtifactRevision.version))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_revisions(
        self, tenant_id: str, client_id: UUID, artifact_id: UUID
    ) -> list[ArtifactRevision]:
        """List all revisions for an artifact, newest first."""
        stmt = (
            select(ArtifactRevision)
            .where(
                ArtifactRevision.tenant_id == tenant_id,
                ArtifactRevision.client_id == client_id,
                ArtifactRevision.artifact_id == artifact_id,
            )
            .order_by(desc(ArtifactRevision.version))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ReviewRepository(ClientScopedRepository[ReviewDecision]):
    """Repository for artifact review decisions."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ReviewDecision)

    async def record_review(
        self,
        tenant_id: str,
        client_id: UUID,
        revision_id: UUID,
        scope: str,
        item_hash: str,
        decision: str,
        actor: str,
        item_key: str | None = None,
        reason: str | None = None,
    ) -> ReviewDecision:
        """Record artifact or item review decision."""
        review = ReviewDecision(
            tenant_id=tenant_id,
            client_id=client_id,
            revision_id=revision_id,
            scope=scope,
            item_key=item_key,
            item_hash=item_hash,
            decision=decision,
            actor=actor,
            reason=reason,
            recorded_at=datetime.now(UTC),
        )
        self.session.add(review)
        await self.session.flush()
        return review

    async def get_reviews_for_revision(
        self, tenant_id: str, client_id: UUID, revision_id: UUID
    ) -> list[ReviewDecision]:
        """Get all reviews for a revision, newest first."""
        stmt = (
            select(ReviewDecision)
            .where(
                ReviewDecision.tenant_id == tenant_id,
                ReviewDecision.client_id == client_id,
                ReviewDecision.revision_id == revision_id,
            )
            .order_by(desc(ReviewDecision.recorded_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
