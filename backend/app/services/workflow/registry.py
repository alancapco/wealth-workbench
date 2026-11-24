"""Skill registry - versioned skill catalog per Architecture §6.2.

Persisted immutable skill_versions plus code handler allowlist.
No arbitrary executable code from DB.
"""
import json
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SkillVersion
from app.schemas.workflow import SkillDescriptor


class SkillRegistry:
    """Versioned skill catalog with handler allowlist."""

    def __init__(self, session: AsyncSession):
        self.session = session
        # Handler allowlist - only these handlers can be invoked
        self.allowed_handlers = {
            "brief.generate",
            "brief.review",
            "context.resolve",
            "transcript.extract",
            "outcomes.review",
            "priority.reason",
            "message.draft",
            "message.review",
            "product.interpret",
            "product.search",
            "suitability.assess",
            "recommendation.review",
            "meeting.capture",
            "notes.manual",
        }

    async def get_skill(
        self,
        tenant_id: str,
        skill_id: str,
        version: str,
    ) -> SkillVersion | None:
        """Get skill version by ID and version."""
        stmt = select(SkillVersion).where(
            SkillVersion.tenant_id == tenant_id,
            SkillVersion.skill_id == skill_id,
            SkillVersion.version == version
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_skill_for_stage(
        self,
        tenant_id: str,
        stage_key: str,
    ) -> SkillVersion | None:
        """Resolve the newest registered skill for a stage and load that version.

        A stage key names either a skill_id or a handler_key; the version is never
        guessed because stage_runs has a composite FK to skill_versions.
        """
        stmt = (
            select(SkillVersion.skill_id, SkillVersion.version)
            .where(
                SkillVersion.tenant_id == tenant_id,
                or_(
                    SkillVersion.skill_id == stage_key,
                    SkillVersion.handler_key == stage_key,
                ),
            )
            .order_by(SkillVersion.created_at.desc(), SkillVersion.version.desc())
            .limit(1)
        )
        row = (await self.session.execute(stmt)).first()
        if row is None:
            return None
        return await self.get_skill(tenant_id, row.skill_id, row.version)

    async def list_skills(
        self,
        tenant_id: str,
        permissions: list[str],
    ) -> list[SkillDescriptor]:
        """List visible allowed skills per API-030.
        
        Only skills matching user permissions are returned.
        Handler key must be in allowlist.
        """
        stmt = select(SkillVersion).where(
            SkillVersion.tenant_id == tenant_id
        )
        result = await self.session.execute(stmt)
        skills = result.scalars().all()
        
        descriptors = []
        granted = set(permissions)
        for skill in skills:
            # Parse descriptor JSON (stored as text in model)
            descriptor_data = json.loads(skill.descriptor)
            
            # Verify handler is allowed
            if skill.handler_key not in self.allowed_handlers:
                continue
            
            # A skill is visible only when the caller holds every permission its
            # descriptor declares; an empty list means no extra grant is required.
            if not granted.issuperset(descriptor_data.get("required_permissions", [])):
                continue
            
            descriptors.append(SkillDescriptor(
                id=skill.skill_id,
                version=skill.version,
                input_kind=descriptor_data.get("input_kind", []),
                output_kind=descriptor_data.get("output_kind", []),
                required_permissions=descriptor_data.get("required_permissions", []),
                policy_keys=descriptor_data.get("policy_keys", []),
                flag_key=descriptor_data.get("flag_key"),
                model_ref=descriptor_data.get("model_ref"),
                prompt_ref=None,  # Would parse ConfigRef if present
                deterministic_rule_ref=None,
                timeout_policy_ref=None,
            ))
        
        return descriptors

    def validate_handler(self, handler_key: str) -> bool:
        """Validate handler is in allowlist.
        
        No arbitrary executable code from DB.
        """
        return handler_key in self.allowed_handlers

    async def register_skill(
        self,
        tenant_id: str,
        skill_id: str,
        version: str,
        handler_key: str,
        descriptor: dict[str, Any],
        content_hash: str,
    ) -> SkillVersion:
        """Register new skill version (admin operation).
        
        Handler must be in allowlist.
        """
        if not self.validate_handler(handler_key):
            raise ValueError(f"Handler {handler_key} not in allowlist")
        
        skill = SkillVersion(
            tenant_id=tenant_id,
            skill_id=skill_id,
            version=version,
            handler_key=handler_key,
            descriptor=json.dumps(descriptor),
            content_hash=content_hash
        )
        
        self.session.add(skill)
        await self.session.flush()
        return skill
