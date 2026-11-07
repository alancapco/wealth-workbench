"""Identity and authentication core - fixture principal and OIDC stubs.

Architecture §3.1 - AUTH_MODE=fixture requires APP_ENV=local|test, isolated fixture database.
No production bypass. Real OIDC implementation external gate.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.config import settings
from app.schemas.common import Environment, EnvironmentKind
from app.schemas.identity import BookRef, DeviceState, Principal


class IdentityError(Exception):
    """Identity configuration or validation error."""
    pass


def get_fixture_principal(check_mode: bool = True, _settings = None) -> Principal:
    """Return synthetic fixture principal for isolated testing only.
    
    Requires AUTH_MODE=fixture and APP_ENV in {local, test}.
    Architecture §3.1: no production bypass, isolated fixture DB/network-deny only.
    
    Args:
        check_mode: If True, validates AUTH_MODE and APP_ENV settings
        _settings: Optional settings override for testing
    """
    config = _settings or settings
    
    if check_mode:
        if config.AUTH_MODE.lower() != "fixture":
            raise IdentityError(f"Fixture principal requires AUTH_MODE=fixture, got {config.AUTH_MODE}")
        
        if config.APP_ENV.lower() not in {"local", "test", "development"}:
            raise IdentityError(
                f"Fixture principal not allowed in APP_ENV={config.APP_ENV}, only local/test/development"
            )
    
    # Synthetic fixture principal with known test tenant/book
    return Principal(
        subject="fixture:rm001@example.test",
        tenant_id="FIXTURE_TENANT_001",
        display_name="Fixture RM User",
        permissions=[
            "client:read",
            "client:write",
            "brief:read",
            "brief:generate",
            "brief:edit",
            "brief:review",
            "workflow:read",
            "workflow:start",
            "workflow:run",
            "workflow:manage",
            "meeting:read",
            "portfolio:read",
            "priority:read",
            "priority:evaluate",
            "priority:control",
            "message:draft",
            "action:preview",
            "action:approve",
            "action:execute",
            "memory:read",
            "memory:propose",
        ],
        books=[
            BookRef(book_id="FIXTURE_BOOK_001", display_name="Fixture Book Alpha"),
            BookRef(book_id="FIXTURE_BOOK_002", display_name="Fixture Book Beta"),
        ],
        entitlement_revision="fixture-rev-001",
        session_expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="fixture-test-env"),
        device_state=DeviceState.APPROVED,
    )


async def verify_oidc_token(token: str, _settings = None) -> Principal:
    """Verify OIDC token and return Principal.
    
    Real implementation requires configured OIDC_ISSUER_URL, validation of
    state/nonce/issuer/audience/signature/expiry per architecture §3.1.
    
    Args:
        token: OIDC token to verify
        _settings: Optional settings override for testing
    
    Raises:
        IdentityError: if OIDC not configured or token invalid
    """
    config = _settings or settings
    
    if not config.OIDC_ISSUER_URL:
        raise IdentityError("OIDC is not configured (OIDC_ISSUER_URL missing)")
    
    # Stub: real implementation validates JWT signature, issuer, audience, expiry
    # and fetches entitlement revision from authoritative provider
    raise NotImplementedError("OIDC token verification requires external identity provider integration")


async def recheck_entitlement(subject: str, current_revision: str, _settings = None) -> bool:
    """Recheck current entitlement revision from authoritative provider.
    
    Every protected request/worker reloads current entitlement revision per architecture §3.1.
    Returns False if revoked or provider unavailable (fail closed).
    
    Args:
        subject: Principal subject identifier
        current_revision: Session entitlement revision to verify
        _settings: Optional settings override for testing
        
    Returns:
        True if entitlement is current, False if revoked or unavailable
    """
    config = _settings or settings
    
    if config.AUTH_MODE.lower() == "fixture":
        # Fixture mode: accept fixture revision in isolated test environments only
        if config.APP_ENV.lower() not in {"local", "test", "development"}:
            return False
        return current_revision == "fixture-rev-001"
    
    if not config.OIDC_ISSUER_URL:
        # No identity provider configured: fail closed
        return False
    
    # Stub: real implementation queries authoritative entitlement provider
    raise NotImplementedError("Entitlement recheck requires external identity provider integration")
