from __future__ import annotations

from fastapi import APIRouter

from app.core.database import get_supabase, get_user_client
from app.core.errors import APIError, error_response
from app.schemas.trips import (
    AuthResponse,
    ProfileOut,
    RefreshRequest,
    SessionTokens,
    SignInRequest,
    SignUpRequest,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _session_tokens(session) -> SessionTokens:
    return SessionTokens(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in or 3600,
    )


def _fetch_profile(access_token: str, user_id: str) -> ProfileOut | None:
    client = get_user_client(access_token)
    response = (
        client.table("profiles")
        .select("id, email, full_name, avatar_url, created_at, updated_at")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if not response.data:
        return None
    return ProfileOut(**response.data)


@router.post("/sign-up", response_model=AuthResponse)
def sign_up(payload: SignUpRequest) -> AuthResponse:
    supabase = get_supabase()
    try:
        result = supabase.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password,
            }
        )
    except Exception as err:  # gotrue raises broad exception types
        message = str(err).lower()
        if "already registered" in message or "already exists" in message:
            return AuthResponse(error="An account with this email already exists.")
        if "password" in message:
            return AuthResponse(error=str(err))
        return AuthResponse(error="Could not create the account. Please try again.")

    if not result.user:
        return AuthResponse(error="Could not create the account. Please try again.")

    # Email confirmation is off in this project, so a session is returned.
    if not result.session:
        return AuthResponse(error="Please confirm your email before signing in.")

    # Create the profile row as the signed-in user (RLS allows inserting
    # your own profile row).
    try:
        client = get_user_client(result.session.access_token)
        (
            client.table("profiles")
            .upsert(
                {
                    "id": result.user.id,
                    "email": payload.email,
                    "full_name": payload.full_name,
                }
            )
            .execute()
        )
    except Exception:
        # Sign-up succeeded; a missing profile row is not fatal here.
        pass

    return AuthResponse(
        session=_session_tokens(result.session),
        profile=_fetch_profile(result.session.access_token, result.user.id),
        error=None,
    )


@router.post("/sign-in", response_model=AuthResponse)
def sign_in(payload: SignInRequest) -> AuthResponse:
    supabase = get_supabase()
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception:
        return AuthResponse(error="Invalid email or password.")

    if not result.session or not result.user:
        return AuthResponse(error="Invalid email or password.")

    return AuthResponse(
        session=_session_tokens(result.session),
        profile=_fetch_profile(result.session.access_token, result.user.id),
        error=None,
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest) -> AuthResponse:
    supabase = get_supabase()
    try:
        result = supabase.auth.refresh_session(payload.refresh_token)
    except Exception:
        return AuthResponse(error="Invalid or expired refresh token.")

    if not result.session or not result.user:
        return AuthResponse(error="Invalid or expired refresh token.")

    return AuthResponse(
        session=_session_tokens(result.session),
        profile=_fetch_profile(result.session.access_token, result.user.id),
        error=None,
    )
