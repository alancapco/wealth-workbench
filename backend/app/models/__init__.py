"""ORM models for RM Workbench persistence layer.

All models imported here are registered with SQLAlchemy metadata for Alembic discovery.
"""
from app.core.database import Base

# Legacy models
from app.models.models import AuditLog, Brief, Client, Holding, Interaction

# Platform and tenant scope
from app.models.platform import Book, ClientAssignment, ClientScope, WorkbenchTenant

# Workflow orchestration
from app.models.workflow import CalendarEvent, Meeting, SkillVersion, StageRun, Workflow

# Artifact lineage and revisions
from app.models.artifact import (
    ArtifactDependency,
    ArtifactItem,
    ArtifactLineage,
    ArtifactRevision,
    ReviewDecision,
    RevisionSource,
    SourceEvidence,
    StageArtifactRef,
)

# Action platform
from app.models.action import (
    ActionAuthorization,
    ActionPreview,
    ClientMemoryEntry,
    OutboxAction,
    OutboxAttempt,
)

# Admin, config, audit, telemetry
from app.models.admin import (
    AuditChainHead,
    AuditEvent,
    CapabilityControl,
    ConfigScope,
    ConfigurationApproval,
    ConfigurationRevision,
    GovernanceEvidence,
    IdempotencyRequest,
    TelemetryEvent,
)

# Priority
from app.models.priority import (
    ContactOutcome,
    PriorityControl,
    PriorityEvaluation,
    PriorityItem,
)

# Product
from app.models.product import (
    CandidateSelection,
    SuitabilityOverride,
)

# Capture
from app.models.capture import (
    CaptureSession,
    ConsentRecord,
)

# Shariah pilot (default OFF, DEC-05 gated)
from app.models.shariah import (
    ShariahEstimate,
    ShariahEvidence,
)

# Family pilot (default OFF, DEC-06/DEC-07 gated)
from app.models.family import (
    FamilyRelationship,
    HouseholdGroup,
    HouseholdMembership,
)

# Demo client data (replaces HubSpot)
from app.models.client_data import (
    DemoClient,
    ClientPortfolioHolding,
    ClientFinancialPlan,
    ClientConversation,
    ClientSuitabilityProfile,
)

__all__ = [
    "Base",
    # Legacy
    "Client",
    "Holding",
    "Interaction",
    "Brief",
    "AuditLog",
    # Platform
    "WorkbenchTenant",
    "Book",
    "ClientScope",
    "ClientAssignment",
    # Workflow
    "CalendarEvent",
    "Meeting",
    "Workflow",
    "SkillVersion",
    "StageRun",
    # Artifact
    "ArtifactLineage",
    "ArtifactRevision",
    "ArtifactItem",
    "ArtifactDependency",
    "StageArtifactRef",
    "SourceEvidence",
    "RevisionSource",
    "ReviewDecision",
    # Action
    "ActionPreview",
    "ActionAuthorization",
    "OutboxAction",
    "OutboxAttempt",
    "ClientMemoryEntry",
    # Admin
    "ConfigScope",
    "ConfigurationRevision",
    "GovernanceEvidence",
    "ConfigurationApproval",
    "CapabilityControl",
    "IdempotencyRequest",
    "AuditEvent",
    "AuditChainHead",
    "TelemetryEvent",
    # Priority
    "PriorityEvaluation",
    "PriorityItem",
    "PriorityControl",
    "ContactOutcome",
    # Product
    "CandidateSelection",
    "SuitabilityOverride",
    # Capture
    "ConsentRecord",
    "CaptureSession",
    # Shariah pilot
    "ShariahEvidence",
    "ShariahEstimate",
    # Family pilot
    "FamilyRelationship",
    "HouseholdGroup",
    "HouseholdMembership",
    # Demo client data
    "DemoClient",
    "ClientPortfolioHolding",
    "ClientFinancialPlan",
    "ClientConversation",
    "ClientSuitabilityProfile",
]
