"""Test authorization and scope validation.

Architecture §3.1, §3.3 - tenant/book/client authorization, fixture mode restrictions.
"""
from uuid import UUID, uuid4

import pytest

from app.core.authorization import (
    AuthorizationError,
    check_book_access,
    check_permission,
    check_tenant_scope,
    verify_client_access,
    verify_context_revision,
)
from app.core.identity import IdentityError, get_fixture_principal
from app.schemas.common import Environment, EnvironmentKind, Scope
from app.schemas.identity import BookRef, DeviceState, Principal


@pytest.fixture
def fixture_principal() -> Principal:
    """Return synthetic fixture principal for testing."""
    # Skip mode check in tests - we're testing the principal structure itself
    return get_fixture_principal(check_mode=False)


@pytest.fixture
def minimal_principal() -> Principal:
    """Return minimal principal with no permissions or books."""
    from datetime import datetime, timedelta, timezone
    
    return Principal(
        subject="test:user@example.test",
        tenant_id="TEST_TENANT",
        display_name="Test User",
        permissions=[],
        books=[],
        entitlement_revision="test-rev-001",
        session_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        environment=Environment(kind=EnvironmentKind.FIXTURE, id="test"),
        device_state=DeviceState.APPROVED,
    )


class TestPermissionCheck:
    """Test permission validation."""
    
    def test_permission_granted(self, fixture_principal):
        """Principal has required permission."""
        check_permission(fixture_principal, "client:read")
        # No exception raised
    
    def test_permission_denied(self, minimal_principal):
        """Principal lacks required permission."""
        with pytest.raises(AuthorizationError, match="Permission denied"):
            check_permission(minimal_principal, "client:read")
    
    def test_multiple_permissions(self, fixture_principal):
        """Check multiple permissions individually."""
        check_permission(fixture_principal, "client:read")
        check_permission(fixture_principal, "brief:generate")
        check_permission(fixture_principal, "workflow:start")


class TestBookAccess:
    """Test book-level access control."""
    
    def test_book_access_granted(self, fixture_principal):
        """Principal has access to assigned book."""
        check_book_access(fixture_principal, "FIXTURE_BOOK_001")
        check_book_access(fixture_principal, "FIXTURE_BOOK_002")
    
    def test_book_access_denied(self, fixture_principal):
        """Principal lacks access to unassigned book."""
        with pytest.raises(AuthorizationError, match="Book access denied"):
            check_book_access(fixture_principal, "UNASSIGNED_BOOK")
    
    def test_no_books_assigned(self, minimal_principal):
        """Principal with no book assignments denied all books."""
        with pytest.raises(AuthorizationError):
            check_book_access(minimal_principal, "ANY_BOOK")


class TestTenantScope:
    """Test tenant scope validation per architecture §3.3."""
    
    def test_tenant_match(self, fixture_principal):
        """Scope tenant matches principal tenant."""
        scope = Scope(tenant_id="FIXTURE_TENANT_001")
        check_tenant_scope(fixture_principal, scope)
    
    def test_tenant_mismatch(self, fixture_principal):
        """Cross-tenant access denied per architecture §3.3."""
        scope = Scope(tenant_id="OTHER_TENANT")
        
        with pytest.raises(AuthorizationError, match="Tenant mismatch"):
            check_tenant_scope(fixture_principal, scope)
    
    def test_tenant_and_book_match(self, fixture_principal):
        """Scope with matching tenant and book."""
        scope = Scope(
            tenant_id="FIXTURE_TENANT_001",
            book_id="FIXTURE_BOOK_001",
        )
        check_tenant_scope(fixture_principal, scope)
    
    def test_tenant_match_book_denied(self, fixture_principal):
        """Tenant matches but book access denied."""
        scope = Scope(
            tenant_id="FIXTURE_TENANT_001",
            book_id="UNASSIGNED_BOOK",
        )
        
        with pytest.raises(AuthorizationError, match="Book access denied"):
            check_tenant_scope(fixture_principal, scope)
    
    def test_tenant_and_jurisdiction(self, fixture_principal):
        """Scope with tenant and jurisdiction."""
        scope = Scope(
            tenant_id="FIXTURE_TENANT_001",
            jurisdiction="US-NY",
        )
        check_tenant_scope(fixture_principal, scope)


class TestClientAccess:
    """Test client-level access control."""
    
    def test_client_same_tenant(self, fixture_principal):
        """Client in same tenant accessible."""
        client_id = uuid4()
        verify_client_access(
            fixture_principal,
            tenant_id="FIXTURE_TENANT_001",
            client_id=client_id,
        )
    
    def test_client_cross_tenant_denied(self, fixture_principal):
        """Client in different tenant denied (indistinguishable from not found)."""
        client_id = uuid4()
        
        with pytest.raises(AuthorizationError, match="Client not found or access denied"):
            verify_client_access(
                fixture_principal,
                tenant_id="OTHER_TENANT",
                client_id=client_id,
            )
    
    def test_client_with_book_access(self, fixture_principal):
        """Client in same tenant and accessible book."""
        client_id = uuid4()
        verify_client_access(
            fixture_principal,
            tenant_id="FIXTURE_TENANT_001",
            client_id=client_id,
            book_id="FIXTURE_BOOK_001",
        )
    
    def test_client_with_book_denied(self, fixture_principal):
        """Client in same tenant but inaccessible book denied."""
        client_id = uuid4()
        
        with pytest.raises(AuthorizationError, match="Client not found or access denied"):
            verify_client_access(
                fixture_principal,
                tenant_id="FIXTURE_TENANT_001",
                client_id=client_id,
                book_id="UNASSIGNED_BOOK",
            )
    
    def test_unauthorized_indistinguishable_from_not_found(self, fixture_principal):
        """Architecture §3.1: unauthorized/nonexistent return indistinguishable 404."""
        client_id = uuid4()
        
        # Both cross-tenant and wrong-book raise same generic error
        with pytest.raises(AuthorizationError, match="Client not found or access denied"):
            verify_client_access(fixture_principal, "OTHER_TENANT", client_id)
        
        with pytest.raises(AuthorizationError, match="Client not found or access denied"):
            verify_client_access(
                fixture_principal,
                "FIXTURE_TENANT_001",
                client_id,
                book_id="WRONG_BOOK",
            )


class TestContextRevision:
    """Test context revision validation per architecture §4.2."""
    
    def test_context_revision_current(self):
        """Current context revision matches."""
        verify_context_revision(current_revision=5, required_revision=5)
    
    def test_context_revision_stale(self):
        """Stale context revision invalidates operation."""
        with pytest.raises(AuthorizationError, match="Context changed"):
            verify_context_revision(current_revision=6, required_revision=5)
    
    def test_context_revision_future(self):
        """Future required revision also fails (invalid state)."""
        with pytest.raises(AuthorizationError, match="Context changed"):
            verify_context_revision(current_revision=5, required_revision=6)


class TestFixtureMode:
    """Test fixture mode restrictions per architecture §3.1."""
    
    def test_fixture_principal_in_local_env(self, monkeypatch):
        """Fixture principal allowed in local environment."""
        from app.core import config, identity
        
        # Reload settings with fixture mode
        monkeypatch.setenv("AUTH_MODE", "fixture")
        monkeypatch.setenv("APP_ENV", "local")
        settings_instance = config.Settings()
        
        principal = identity.get_fixture_principal(_settings=settings_instance)
        assert principal.subject.startswith("fixture:")
        assert principal.tenant_id == "FIXTURE_TENANT_001"
        assert principal.environment.kind == EnvironmentKind.FIXTURE
    
    def test_fixture_principal_in_test_env(self, monkeypatch):
        """Fixture principal allowed in test environment."""
        from app.core import config, identity
        
        monkeypatch.setenv("AUTH_MODE", "fixture")
        monkeypatch.setenv("APP_ENV", "test")
        settings_instance = config.Settings()
        
        principal = identity.get_fixture_principal(_settings=settings_instance)
        assert principal.subject.startswith("fixture:")
    
    def test_fixture_principal_rejected_in_production(self, monkeypatch):
        """Architecture §3.1: fixture mode rejected in production."""
        from app.core import config
        
        monkeypatch.setenv("AUTH_MODE", "fixture")
        monkeypatch.setenv("APP_ENV", "production")
        
        # Settings validation should reject this at init
        with pytest.raises(ValueError, match="AUTH_MODE=fixture is not allowed"):
            config.Settings()
    
    def test_fixture_requires_auth_mode_fixture(self, monkeypatch):
        """Fixture principal requires AUTH_MODE=fixture."""
        from app.core import config, identity
        
        monkeypatch.setenv("AUTH_MODE", "oidc")
        monkeypatch.setenv("APP_ENV", "local")
        settings_instance = config.Settings()
        
        with pytest.raises(IdentityError, match="Fixture principal requires AUTH_MODE=fixture"):
            identity.get_fixture_principal(_settings=settings_instance)
    
    def test_fixture_principal_has_test_permissions(self, fixture_principal):
        """Fixture principal includes test permissions."""
        # Architecture §3.1: synthetic fixture with known permissions
        assert "client:read" in fixture_principal.permissions
        assert "brief:generate" in fixture_principal.permissions
        assert "workflow:start" in fixture_principal.permissions
        assert len(fixture_principal.books) == 2
    
    def test_fixture_principal_device_approved(self, fixture_principal):
        """Fixture principal has approved device state."""
        assert fixture_principal.device_state == DeviceState.APPROVED
    
    def test_fixture_principal_session_not_expired(self, fixture_principal):
        """Fixture principal session has future expiry."""
        from datetime import datetime, timezone
        
        assert fixture_principal.session_expires_at > datetime.now(timezone.utc)


class TestOIDCStubs:
    """Test OIDC stub behavior (real implementation external gate)."""
    
    @pytest.mark.asyncio
    async def test_oidc_not_configured(self, monkeypatch):
        """OIDC verification fails when not configured."""
        from app.core import config, identity
        
        monkeypatch.setenv("AUTH_MODE", "oidc")
        monkeypatch.setenv("OIDC_ISSUER_URL", "")
        config.settings = config.Settings()
        
        with pytest.raises(IdentityError, match="OIDC is not configured"):
            await identity.verify_oidc_token("fake-token")
    
    @pytest.mark.asyncio
    async def test_oidc_verification_not_implemented(self, monkeypatch):
        """OIDC verification is stub awaiting external integration."""
        from app.core import config, identity
        
        monkeypatch.setenv("AUTH_MODE", "oidc")
        monkeypatch.setenv("OIDC_ISSUER_URL", "https://idp.example.com")
        monkeypatch.setenv("OIDC_CLIENT_ID", "client-123")
        monkeypatch.setenv("OIDC_CLIENT_SECRET", "secret-abc")
        settings_instance = config.Settings()
        
        with pytest.raises(NotImplementedError, match="external identity provider"):
            await identity.verify_oidc_token("fake-token", _settings=settings_instance)
    
    @pytest.mark.asyncio
    async def test_entitlement_recheck_fixture_mode(self, monkeypatch):
        """Entitlement recheck accepts fixture revision in fixture mode."""
        from app.core import config, identity
        
        monkeypatch.setenv("AUTH_MODE", "fixture")
        monkeypatch.setenv("APP_ENV", "test")
        settings_instance = config.Settings()
        
        result = await identity.recheck_entitlement(
            subject="fixture:rm001@example.test",
            current_revision="fixture-rev-001",
            _settings=settings_instance,
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_entitlement_recheck_fixture_wrong_revision(self, monkeypatch):
        """Entitlement recheck rejects wrong fixture revision."""
        from app.core import config, identity
        
        monkeypatch.setenv("AUTH_MODE", "fixture")
        monkeypatch.setenv("APP_ENV", "test")
        settings_instance = config.Settings()
        
        result = await identity.recheck_entitlement(
            subject="fixture:rm001@example.test",
            current_revision="wrong-revision",
            _settings=settings_instance,
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_entitlement_recheck_not_configured(self, monkeypatch):
        """Entitlement recheck fails closed when not configured."""
        from app.core import config, identity
        
        monkeypatch.setenv("AUTH_MODE", "oidc")
        monkeypatch.setenv("OIDC_ISSUER_URL", "")
        settings_instance = config.Settings()
        
        result = await identity.recheck_entitlement(
            subject="user@example.com",
            current_revision="rev-123",
            _settings=settings_instance,
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_entitlement_recheck_not_implemented(self, monkeypatch):
        """Entitlement recheck is stub awaiting external integration."""
        from app.core import config, identity
        
        monkeypatch.setenv("AUTH_MODE", "oidc")
        monkeypatch.setenv("OIDC_ISSUER_URL", "https://idp.example.com")
        monkeypatch.setenv("OIDC_CLIENT_ID", "test")
        monkeypatch.setenv("OIDC_CLIENT_SECRET", "test")
        settings_instance = config.Settings()
        
        with pytest.raises(NotImplementedError, match="external identity provider"):
            await identity.recheck_entitlement("user@example.com", "rev-123", _settings=settings_instance)
