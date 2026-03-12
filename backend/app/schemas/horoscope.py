"""
Pydantic V2 schemas for horoscope and numerology endpoints.
"""
from datetime import date

from pydantic import BaseModel


# ── Horoscope responses ───────────────────────────────────────────────────────

class DailyHoroscopeResponse(BaseModel):
    zodiac_sign: str
    date: str          # ISO date string
    horoscope: str
    language: str


class WeeklyHoroscopeResponse(BaseModel):
    zodiac_sign: str
    week_start: str    # ISO date of Monday
    week_end: str      # ISO date of Sunday
    horoscope: str
    language: str


# ── Numerology responses ──────────────────────────────────────────────────────

class NumberInfoResponse(BaseModel):
    name_en: str
    name_es: str
    keywords_en: list[str]
    keywords_es: list[str]
    description_en: str
    description_es: str
    strengths_en: list[str]
    strengths_es: list[str]
    challenges_en: list[str]
    challenges_es: list[str]


class NumerologyProfileResponse(BaseModel):
    life_number: int
    personal_year: int
    personal_month: int
    life_number_info: NumberInfoResponse | None
    birth_date: date
