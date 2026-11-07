"""Identity and session contracts - Principal, authorization context.

Architecture §3.1 AUTH-01..03, API-001.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.schemas.common import CapabilityState, Environment


class DeviceState(str, Enum):
    APPROVED = "APPROVED"
    UNCONFIGURED = "UNCONFIGURED"
    DENIED = "DENIED"


class BookRef(BaseModel):
    """Opaque institutional book identifier."""
    model_config = ConfigDict(extra="forbid")
    
    book_id: str
    display_name: str | None = None


class Principal(BaseModel):
    """Verified authenticated principal per architecture §3.1."""
    model_config = ConfigDict(extra="forbid")
    
    subject: str
    tenant_id: str
    display_name: str
    permissions: list[str]
    books: list[BookRef]
    entitlement_revision: str
    session_expires_at: datetime
    environment: Environment
    device_state: DeviceState
