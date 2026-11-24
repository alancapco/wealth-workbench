"""Product artifact persistence.

`ArtifactRepository` exposes lineage/revision primitives but not the two
operations the product routes use. Extending it keeps tenant/client scoping in
the repository layer instead of duplicating artifact writes in the endpoints.
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select

from app.models.artifact import ArtifactLineage, ArtifactRevision
from app.repositories.artifacts import ArtifactRepository
from app.schemas.common import ArtifactRef, Environment
from app.services.product.config_refs import canonical_hash, canonical_json


class ProductArtifactRepository(ArtifactRepository):
    """Artifact reads/writes for the product endpoints."""

    async def get_artifact(self, tenant_id: str, artifact_id: UUID) -> dict | None:
        lineage = (await self.session.execute(
            select(ArtifactLineage).where(
                ArtifactLineage.tenant_id == tenant_id,
                ArtifactLineage.id == artifact_id,
            )
        )).scalar_one_or_none()
        if lineage is None or lineage.current_revision_id is None:
            return None
        revision = (await self.session.execute(
            select(ArtifactRevision).where(
                ArtifactRevision.tenant_id == tenant_id,
                ArtifactRevision.id == lineage.current_revision_id,
            )
        )).scalar_one_or_none()
        if revision is None:
            return None
        return {
            "payload": revision.payload,
            "client_id": str(lineage.client_id),
            "workflow_id": str(lineage.workflow_id),
        }

    async def create_artifact(
        self,
        tenant_id: str,
        client_id: UUID,
        workflow_id: UUID,
        kind: str,
        payload: dict,
        created_by: str,
        environment: Environment,
    ) -> ArtifactRef:
        now = datetime.now(UTC)
        lineage = ArtifactLineage(
            id=uuid4(),
            tenant_id=tenant_id,
            client_id=client_id,
            workflow_id=workflow_id,
            kind=kind,
            created_by=created_by,
            created_at=now,
        )
        self.session.add(lineage)
        await self.session.flush()

        revision = ArtifactRevision(
            id=uuid4(),
            tenant_id=tenant_id,
            client_id=client_id,
            artifact_id=lineage.id,
            version=1,
            content_hash=canonical_hash(payload),
            payload=canonical_json(payload),
            environment_kind=environment.kind.value,
            environment_id=environment.id,
            created_by=created_by,
            created_at=now,
        )
        self.session.add(revision)
        await self.session.flush()
        lineage.current_revision_id = revision.id

        # Product routes return immediately after this call; commit here so the
        # artifact and its current revision are durable.
        await self.session.commit()
        return ArtifactRef(
            artifact_id=lineage.id,
            revision_id=revision.id,
            version=1,
            hash=revision.content_hash,
        )
