"""
Pydantic V2 schemas for tarot and compatibility endpoints.
All inputs use strict validation; no unexpected fields are accepted.
"""
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────

class DailyReadingRequest(BaseModel):
    """Optional parameters for retrieving / generating the daily reading."""
    model_config = ConfigDict(extra="forbid")

    spread_type: str = "past_present_future"
    language: str | None = None  # falls back to user's preferred_language

    @field_validator("spread_type")
    @classmethod
    def valid_spread(cls, v: str) -> str:
        allowed = ("past_present_future", "situation_action_outcome")
        if v not in allowed:
            raise ValueError(f"spread_type must be one of {allowed}")
        return v


class AskTarotistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    language: str | None = None

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question cannot be blank")
        if len(v) > 500:
            raise ValueError("question must be 500 characters or fewer")
        return v


class CompatibilityCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    partner_zodiac: str
    partner_birth_date: date | None = None
    language: str | None = None

    @field_validator("partner_zodiac")
    @classmethod
    def valid_zodiac(cls, v: str) -> str:
        from app.services.astrology import VALID_SIGNS
        if v not in VALID_SIGNS:
            raise ValueError(f"partner_zodiac must be a valid zodiac sign, got {v!r}")
        return v


# ── Responses ─────────────────────────────────────────────────────────────────

class DrawnCardResponse(BaseModel):
    id: int
    name: str
    name_es: str
    arcana: str
    suit: str | None
    orientation: str
    position: str
    keywords_en: list[str]
    keywords_es: list[str]


class DailyReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reading_date: date
    spread_type: str
    cards_drawn: list[Any]
    ai_interpretation: str
    language: str
    created_at: datetime


class TarotistAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    answer: str
    language: str
    asked_at: datetime


class ReadingHistoryResponse(BaseModel):
    readings: list[DailyReadingResponse]
    total: int
    page: int
    page_size: int


class CompatibilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    partner_zodiac: str
    compatibility_score: int
    ai_interpretation: str
    language: str
    created_at: datetime


class CompatibilityHistoryResponse(BaseModel):
    readings: list[CompatibilityResponse]
    total: int
