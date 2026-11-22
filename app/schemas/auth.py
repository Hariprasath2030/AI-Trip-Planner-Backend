from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class SessionTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class ProfileOut(BaseModel):
    id: str
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AuthResponse(BaseModel):
    session: SessionTokens | None = None
    profile: ProfileOut | None = None
    error: str | None = None
