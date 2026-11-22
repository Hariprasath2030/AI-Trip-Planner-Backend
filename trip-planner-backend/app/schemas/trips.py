from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

TripStatus = Literal["Planning", "Upcoming", "Completed"]
ItineraryCategory = Literal["flight", "hotel", "car", "activity", "meal", "extra"]


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


class TripCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=160)
    source: str | None = Field(default=None, max_length=160)
    start_date: date
    end_date: date
    budget: float | None = Field(default=None, ge=0)
    interests: list[str] = Field(default_factory=list)
    travelers: int = Field(default=1, ge=1, le=100)
    description: str | None = Field(default=None, max_length=5000)
    status: TripStatus = "Planning"
    cover_image_path: str | None = Field(default=None, max_length=500)


class TripUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    destination: str | None = Field(default=None, min_length=1, max_length=160)
    source: str | None = Field(default=None, max_length=160)
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = Field(default=None, ge=0)
    interests: list[str] | None = None
    travelers: int | None = Field(default=None, ge=1, le=100)
    description: str | None = Field(default=None, max_length=5000)
    status: TripStatus | None = None
    cover_image_path: str | None = Field(default=None, max_length=500)


class TripOut(BaseModel):
    id: str
    user_id: str
    title: str
    destination: str
    source: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    budget: float | None = None
    interests: list[str] = Field(default_factory=list)
    travelers: int | None = None
    description: str | None = None
    status: str | None = None
    cover_image_path: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ItineraryItemCreate(BaseModel):
    day_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    category: ItineraryCategory
    start_time: str | None = Field(default=None, max_length=8)
    description: str | None = Field(default=None, max_length=5000)
    metadata: dict | None = None


class ItineraryItemUpdate(BaseModel):
    day_number: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=160)
    category: ItineraryCategory | None = None
    start_time: str | None = Field(default=None, max_length=8)
    description: str | None = Field(default=None, max_length=5000)
    metadata: dict | None = None


class ItineraryItemOut(BaseModel):
    id: str
    trip_id: str
    day_number: int
    title: str
    category: str
    start_time: str | None = None
    description: str | None = None
    metadata: dict | None = None
    created_at: str | None = None
    updated_at: str | None = None
