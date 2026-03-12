"""
Pydantic V2 request/response schemas for authentication endpoints.
All inputs use strict validation; no unexpected fields are accepted.
"""
import uuid
from datetime import date, time, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# ─── Requests ────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    full_name: str
    birth_date: date

    # Optional astrological data
    birth_time: time | None = None
    birth_city: str | None = None
    birth_country: str | None = None

    # Preferences
    preferred_language: str = "es"
    timezone: str = "America/Mexico_City"

    # Collected after registration (Step 7 onboarding flow)
    onboarding_answers: dict[str, Any] | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("full_name cannot be blank")
        return v

    @field_validator("preferred_language")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("es", "en"):
            raise ValueError("preferred_language must be 'es' or 'en'")
        return v


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class SocialAuthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str           # "google" | "apple"
    id_token: str           # OAuth ID token from the provider
    full_name: str | None = None
    birth_date: date | None = None
    preferred_language: str = "es"

    @field_validator("provider")
    @classmethod
    def valid_provider(cls, v: str) -> str:
        if v not in ("google", "apple"):
            raise ValueError("provider must be 'google' or 'apple'")
        return v


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    birth_time: time | None = None
    birth_city: str | None = None
    birth_country: str | None = None
    preferred_language: str | None = None
    timezone: str | None = None
    onboarding_answers: dict[str, Any] | None = None

    @field_validator("preferred_language")
    @classmethod
    def valid_language(cls, v: str | None) -> str | None:
        if v is not None and v not in ("es", "en"):
            raise ValueError("preferred_language must be 'es' or 'en'")
        return v


# ─── Responses ───────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    auth_provider: str
    birth_date: date
    zodiac_sign: str | None
    life_number: int | None
    preferred_language: str
    timezone: str
    is_premium: bool
    onboarding_answers: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
