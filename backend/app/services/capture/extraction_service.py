"""Extraction service: AI extraction stub and RM edit persistence."""
from datetime import datetime, UTC
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ArtifactRevision


class ExtractionService:
    """Manage extraction from transcript/notes with RM corrections."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_extraction_artifact(
        self,
        tenant_id: str,
        client_id: UUID,
        artifact_id: UUID,
        revision_id: UUID,
        version: int,
        content_hash: str,
        payload: dict[str, Any],
        environment_kind: str,
        environment_id: str,
        created_by: str,
    ) -> ArtifactRevision:
        """Create extraction artifact revision with items and evidence refs.
        
        Payload structure per API-043/044:
        {
            "basis_ref": {"artifact_id": UUID, "revision_id": UUID, "hash": str},
            "items": [
                {
                    "key": str,
                    "type": "DECISION|ACTION|PREFERENCE|COMMITMENT|FOLLOWUP_TOPIC",
                    "content": str,
                    "owner": {
                        "ref": str|null,
                        "display": str,
                        "origin": "RECORDED|RM_ENTERED"
                    }|null,
                    "due_date": date|null,
                    "due_date_origin": "RECORDED|RM_ENTERED"|null,
                    "evidence_refs": [{"segment_id": UUID, ...}],
                    "confidence": decimal|null,
                    "origin": "DERIVED|RM_ENTERED",
                    "review_state": {...}
                }
            ]
        }
        
        AI extraction is DERIVED with confidence and evidence refs.
        RM edits are RM_ENTERED with explicit owner/date origin.
        """
        revision = ArtifactRevision(
            id=revision_id,
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

    async def apply_extraction_edits(
        self,
        tenant_id: str,
        client_id: UUID,
        artifact_id: UUID,
        current_revision_id: UUID,
        edits: list[dict[str, Any]],
        suppressed_item_keys: list[str],
        actor: str,
    ) -> ArtifactRevision:
        """Apply RM corrections to extraction, creating immutable new revision.
        
        Edit structure per API-044:
        {
            "key": str,
            "content": str,
            "owner": {...},
            "due_date": date|null,
            "due_date_origin": "RECORDED|RM_ENTERED"|null,
            "evidence_refs": [...],
            "reason": {"code": str, "catalog_ref": {...}, "other_text": str|null}
        }
        
        Creates new revision with:
        - Edited items marked origin=RM_ENTERED
        - Suppressed items removed from items list
        - Reason preserved in edit audit
        """
        # Get current revision
        stmt = select(ArtifactRevision).where(
            ArtifactRevision.tenant_id == tenant_id,
            ArtifactRevision.client_id == client_id,
            ArtifactRevision.id == current_revision_id,
        )
        result = await self.session.execute(stmt)
        current = result.scalar_one_or_none()
        
        if not current:
            raise ValueError(f"Current revision {current_revision_id} not found")
        
        # Build new payload with edits applied
        current_payload = current.payload
        items = current_payload.get("items", [])
        
        # Apply edits
        edited_items = []
        for item in items:
            if item["key"] in suppressed_item_keys:
                continue  # Suppressed, exclude from new revision
            
            # Check if this item has an edit
            edit = next((e for e in edits if e["key"] == item["key"]), None)
            if edit:
                # Apply edit, mark as RM_ENTERED
                edited_item = {
                    **item,
                    "content": edit["content"],
                    "owner": edit.get("owner"),
                    "due_date": edit.get("due_date"),
                    "due_date_origin": edit.get("due_date_origin"),
                    "evidence_refs": edit.get("evidence_refs", item.get("evidence_refs", [])),
                    "origin": "RM_ENTERED",
                    "edit_reason": edit.get("reason"),  # Preserve reason
                }
                edited_items.append(edited_item)
            else:
                edited_items.append(item)
        
        new_payload = {
            **current_payload,
            "items": edited_items,
        }
        
        # Calculate new content hash (simplified - real impl would use proper hashing)
        import hashlib
        import json
        new_content_hash = hashlib.sha256(json.dumps(new_payload, sort_keys=True).encode()).hexdigest()
        
        # Create new revision
        new_version = current.version + 1
        new_revision = ArtifactRevision(
            id=UUID,  # Generated by caller
            tenant_id=tenant_id,
            client_id=client_id,
            artifact_id=artifact_id,
            version=new_version,
            content_hash=new_content_hash,
            payload=new_payload,
            environment_kind=current.environment_kind,
            environment_id=current.environment_id,
            created_by=actor,
            created_at=datetime.now(UTC),
        )
        
        self.session.add(new_revision)
        await self.session.flush()
        return new_revision

    async def stub_ai_extraction(
        self,
        basis_content: str,
    ) -> list[dict[str, Any]]:
        """Stub AI extraction - real implementation would call AI model.
        
        Returns synthetic extraction items with DERIVED origin.
        No real AI inference in this stub.
        """
        # Stub: return empty extraction
        # Real implementation would:
        # 1. Call AI model with transcript/notes
        # 2. Parse structured output
        # 3. Link evidence refs to transcript segments
        # 4. Set confidence scores
        return []
