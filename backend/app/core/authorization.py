"""Authorization and scope validation.

Architecture §3.1, §3.3 - tenant/book/client authorization, context revision recheck.
"""
from uuid import UUID

from app.schemas.common import Scope
from app.schemas.identity import Principal


class AuthorizationError(Exception):
    """Authorization check failed."""
    pass


def check_permission(principal: Principal, permission: str) -> None:
    """Check principal has required permission.
    
    Raises:
        AuthorizationError: if permission denied
    """
    if permission not in principal.permissions:
        raise AuthorizationError(f"Permission denied: {permission}")


def check_book_access(principal: Principal, book_id: str) -> None:
    """Check principal has access to specified book.
    
    Args:
        principal: Authenticated principal
        book_id: Book identifier to check
        
    Raises:
        AuthorizationError: if book access denied
    """
    if not any(book.book_id == book_id for book in principal.books):
        raise AuthorizationError(f"Book access denied: {book_id}")


def check_tenant_scope(principal: Principal, scope: Scope) -> None:
    """Check principal tenant matches scope tenant.
    
    Architecture §3.3: tenant never implicit/global, cross-tenant denied.
    
    Args:
        principal: Authenticated principal
        scope: Requested scope
        
    Raises:
        AuthorizationError: if tenant mismatch
    """
    if scope.tenant_id != principal.tenant_id:
        raise AuthorizationError(
            f"Tenant mismatch: principal {principal.tenant_id}, scope {scope.tenant_id}"
        )
    
    # If scope specifies book, verify principal has access
    if scope.book_id is not None:
        check_book_access(principal, scope.book_id)


def verify_client_access(
    principal: Principal,
    tenant_id: str,
    client_id: UUID,
    book_id: str | None = None,
) -> None:
    """Verify principal has access to client within tenant/book context.
    
    Architecture §4.1: client_scope bridge determines accessibility.
    Unauthorized/nonexistent return indistinguishable per §3.1.
    
    Args:
        principal: Authenticated principal
        tenant_id: Client's tenant
        client_id: Client UUID
        book_id: Optional book constraint
        
    Raises:
        AuthorizationError: if access denied (indistinguishable from not found)
    """
    # Tenant must match
    if tenant_id != principal.tenant_id:
        raise AuthorizationError("Client not found or access denied")
    
    # If book specified, principal must have book access
    if book_id is not None:
        try:
            check_book_access(principal, book_id)
        except AuthorizationError:
            raise AuthorizationError("Client not found or access denied")
    
    # Real implementation queries client_scope bridge and verifies current entitlement revision
    # For now, accept in fixture mode with proper tenant
    # Production implementation requires database query with entitlement recheck


def verify_context_revision(
    current_revision: int,
    required_revision: int,
) -> None:
    """Verify context revision matches required revision.
    
    Architecture §4.2: stale context invalidates dependent operations.
    
    Args:
        current_revision: Current context revision
        required_revision: Required context revision for operation
        
    Raises:
        AuthorizationError: if context revision stale
    """
    if current_revision != required_revision:
        raise AuthorizationError(
            f"Context changed: current {current_revision}, required {required_revision}"
        )
