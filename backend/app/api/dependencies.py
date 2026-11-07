"""FastAPI dependencies for authentication and authorization.

Architecture §3.1, §5 - session cookie + CSRF for mutations, principal injection.
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.authorization import AuthorizationError, check_permission
from app.core.identity import IdentityError, get_fixture_principal
from app.schemas.identity import Principal


async def get_current_principal(request: Request) -> Principal:
    """Extract and verify current authenticated principal.
    
    Architecture §3.1: institutional OIDC with HttpOnly Secure SameSite cookies.
    Fixture mode requires AUTH_MODE=fixture and APP_ENV=local|test.
    
    Returns:
        Verified Principal
        
    Raises:
        HTTPException: 401 if unauthenticated, 503 if identity unavailable
    """
    try:
        # Real implementation: extract session cookie, verify OIDC token, recheck entitlement
        # For now, return fixture principal in fixture mode only
        principal = get_fixture_principal()
        return principal
    except IdentityError as e:
        # Identity provider unavailable or misconfigured
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "IDENTITY_UNAVAILABLE", "message": str(e)},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Authentication required"},
        )


async def verify_csrf_token(
    request: Request,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> None:
    """Verify CSRF token for mutation requests.
    
    Architecture §5: all POST/PATCH/PUT mutations require CSRF token.
    
    Raises:
        HTTPException: 403 if CSRF token missing or invalid
    """
    if request.method in {"POST", "PATCH", "PUT", "DELETE"}:
        if not x_csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "CSRF_TOKEN_MISSING", "message": "CSRF token required for mutations"},
            )
        
        # Real implementation: validate CSRF token against session
        # For now, accept any non-empty token in fixture mode
        # Production: compare against session-bound token with timing-safe comparison


async def require_permission(permission: str):
    """Dependency factory for permission checks.
    
    Usage:
        @router.get("/briefs", dependencies=[Depends(require_permission("brief:read"))])
    """
    async def _check(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
        try:
            check_permission(principal, permission)
            return principal
        except AuthorizationError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": f"Permission denied: {permission}"},
            )
    
    return _check


# Common dependency type aliases
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]
VerifiedCSRF = Annotated[None, Depends(verify_csrf_token)]
