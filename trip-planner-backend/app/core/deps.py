from __future__ import annotations

from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.database import get_supabase
from app.core.errors import APIError

bearer_scheme = HTTPBearer(auto_error=False)


def _decode_locally(token: str) -> dict[str, Any] | None:
    """Verify the JWT signature and expiry with SUPABASE_JWT_SECRET."""
    settings = get_settings()
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_signature": True, "verify_exp": True},
        )
    except JWTError:
        return None
    return claims if claims.get("sub") else None


def _validate_remotely(token: str) -> dict[str, Any] | None:
    """Ask the Supabase Auth server whether the token is valid."""
    try:
        user = get_supabase().auth.get_user(token)
    except Exception:
        return None
    if not user or not user.user:
        return None
    return {"sub": user.user.id}


def verify_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Verify the Supabase JWT from the Authorization header and return its claims."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise APIError("Missing or invalid Authorization header", 401)

    token = credentials.credentials
    settings = get_settings()
    settings.validate()

    claims = _decode_locally(token) if settings.supabase_jwt_secret else None
    if claims is None:
        claims = _validate_remotely(token)
    if claims is None:
        raise APIError("Invalid or expired token", 401)

    # Keep the raw token around so handlers can build a token-scoped DB client.
    claims["token"] = token
    return claims


def get_current_user_id(claims: dict[str, Any] = Depends(verify_access_token)) -> str:
    user_id: str | None = claims.get("sub")
    if not user_id:
        raise APIError("Invalid or expired token", 401)
    return user_id
