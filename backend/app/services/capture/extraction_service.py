"""Extraction service: deterministic rule-based extraction and RM edit persistence."""
import hashlib
import json
import re
from datetime import UTC, date, datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.models.artifact import ArtifactRevision


def _canonical_json(data: dict) -> str:
    """Canonical JSON for content hashing and TEXT-column storage.

    Matches MessageService/ActionService/brief-generator/artifacts hashing so
    content_hash values compare correctly across the artifact -> action chain.
    """
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


def _as_payload(value: Any) -> dict:
    """payload is a TEXT column: rows come back as JSON, in-memory rows may be dicts."""
    return json.loads(value) if isinstance(value, str) else value


# Rule order is the classification priority: a line yields one item, so the most
# specific cue wins. Confidence reflects rule strength only, never model output.
_EXTRACTION_RULES: list[tuple[str, re.Pattern, float]] = [
    ("DECISION", re.compile(
        r"\b(?:decided|decision|agreed|approved|resolved|concluded|signed off|finalised|finalized)\b", re.I), 0.90),
    ("COMMITMENT", re.compile(
        r"\b(?:commit(?:ted|ment|s)?|promise(?:d|s)?|pledge(?:d|s)?|undertake|guarantee(?:d|s)?|we will|i will)\b", re.I), 0.90),
    ("PREFERENCE", re.compile(
        r"\b(?:prefer(?:s|red)?|preference|favourite|favorite|would rather|likes|dislikes)\b", re.I), 0.85),
    ("FOLLOWUP_TOPIC", re.compile(
        r"\b(?:follow[\s-]?up|next meeting|revisit|agenda|circle back|discuss later)\b", re.I), 0.80),
    ("ACTION", re.compile(
        r"\b(?:action item|to-?do|task|please|need(?:s)? to|should|must|prepare|schedule|arrange|send|email|call|book)\b", re.I), 0.75),
]

_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_NAMED_DATE = re.compile(
    r"\b(\d{1,2})\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{4})\b",
    re.I,
)
_MONTHS = {name: index for index, name in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1
)}
_OWNER = re.compile(
    r"\b(?:owner|assignee|assigned to|responsible)\s*[:=]\s*([A-Z][\w.'-]+(?:\s+[A-Z][\w.'-]+)?)"
)
_SEGMENT_SPLIT = re.compile(r"[\r\n]+|(?<=[.!?])\s+")


def _extract_due_date(text: str) -> Optional[str]:
    """Return an ISO date only when the text states one; never invent a date."""
    match = _ISO_DATE.search(text)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()
        except ValueError:
            pass

    match = _NAMED_DATE.search(text)
    if match:
        try:
            month = _MONTHS[match.group(2)[:3].lower()]
            return date(int(match.group(3)), month, int(match.group(1))).isoformat()
        except (ValueError, KeyError):
            pass
    return None


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
                    "owner": {...}|null,
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
            payload=_canonical_json(payload),
            environment_kind=environment_kind,
            environment_id=environment_id,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )

        self.session.add(revision)
        await self.session.flush()
        # Callers consume payload as a dict; keep the in-memory contract while the
        # TEXT column holds canonical JSON. set_committed_value avoids a dirty UPDATE.
        set_committed_value(revision, "payload", payload)
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
        stmt = select(ArtifactRevision).where(
            ArtifactRevision.tenant_id == tenant_id,
            ArtifactRevision.client_id == client_id,
            ArtifactRevision.id == current_revision_id,
        )
        result = await self.session.execute(stmt)
        current = result.scalar_one_or_none()

        if not current:
            raise ValueError(f"Current revision {current_revision_id} not found")

        current_payload = _as_payload(current.payload)
        items = current_payload.get("items", [])

        edited_items = []
        for item in items:
            if item["key"] in suppressed_item_keys:
                continue  # Suppressed, exclude from new revision

            edit = next((e for e in edits if e["key"] == item["key"]), None)
            if edit:
                edited_item = {
                    **item,
                    "content": edit["content"],
                    "owner": edit.get("owner"),
                    "due_date": edit.get("due_date"),
                    "due_date_origin": edit.get("due_date_origin"),
                    "evidence_refs": edit.get("evidence_refs", item.get("evidence_refs", [])),
                    "origin": "RM_ENTERED",
                    "edit_reason": edit.get("reason"),
                }
                edited_items.append(edited_item)
            else:
                edited_items.append(item)

        new_payload = {**current_payload, "items": edited_items}
        new_content_hash = hashlib.sha256(_canonical_json(new_payload).encode("utf-8")).hexdigest()

        new_revision = ArtifactRevision(
            id=uuid4(),
            tenant_id=tenant_id,
            client_id=client_id,
            artifact_id=artifact_id,
            version=current.version + 1,
            content_hash=new_content_hash,
            payload=_canonical_json(new_payload),
            environment_kind=current.environment_kind,
            environment_id=current.environment_id,
            created_by=actor,
            created_at=datetime.now(UTC),
        )

        self.session.add(new_revision)
        await self.session.flush()
        set_committed_value(new_revision, "payload", new_payload)
        return new_revision

    async def stub_ai_extraction(
        self,
        basis_content: str,
    ) -> list[dict[str, Any]]:
        """Deterministic rule-based extraction from transcript/notes text.

        No external AI dependency: each statement is classified by explicit cue
        words, and owner/due_date are only populated when literally present in the
        text. Plain text carries no segment ids, so evidence_refs stays empty
        rather than fabricating them.
        """
        if not basis_content or not basis_content.strip():
            return []

        items: list[dict[str, Any]] = []
        for statement in _SEGMENT_SPLIT.split(basis_content):
            content = statement.strip()
            if not content:
                continue

            item_type, confidence = None, None
            for candidate_type, pattern, score in _EXTRACTION_RULES:
                if pattern.search(content):
                    item_type, confidence = candidate_type, score
                    break
            if item_type is None:
                continue

            due_date = _extract_due_date(content)
            owner_match = _OWNER.search(content)
            owner = None
            if owner_match:
                owner = {
                    "ref": None,
                    "display": owner_match.group(1).strip(),
                    "origin": "RECORDED",
                }

            items.append({
                "key": f"item-{len(items) + 1}",
                "type": item_type,
                "content": content,
                "owner": owner,
                "due_date": due_date,
                "due_date_origin": "RECORDED" if due_date else None,
                "evidence_refs": [],
                "confidence": confidence,
                "origin": "DERIVED",
                "review_state": "UNREVIEWED",
            })

        return items
