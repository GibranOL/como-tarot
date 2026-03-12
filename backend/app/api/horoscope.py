"""
Horoscope endpoints.

GET /api/horoscope/daily   → Daily horoscope for the user's zodiac sign
GET /api/horoscope/weekly  → Weekly overview (premium only)
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.db.database import get_session
from app.models.user import User
from app.schemas.horoscope import DailyHoroscopeResponse, WeeklyHoroscopeResponse
from app.security.dependencies import get_current_user, get_premium_user
from app.services.ai import generate_daily_horoscope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/horoscope", tags=["horoscope"])


# ── Daily Horoscope ───────────────────────────────────────────────────────────

@router.get("/daily", response_model=DailyHoroscopeResponse)
def get_daily_horoscope(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Return today's AI-generated horoscope for the user's zodiac sign.

    Horoscopes are the same for all users who share a zodiac sign on a given
    date — ideal for response caching at the CDN layer (post-MVP).
    Available to free and premium users.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    lang = current_user.preferred_language
    zodiac = current_user.zodiac_sign or "Aries"

    horoscope = generate_daily_horoscope(
        zodiac_sign=zodiac,
        current_date=today,
        language=lang,
        onboarding_answers=current_user.onboarding_answers,
    )

    return DailyHoroscopeResponse(
        zodiac_sign=zodiac,
        date=today,
        horoscope=horoscope,
        language=lang,
    )


# ── Weekly Horoscope (premium) ────────────────────────────────────────────────

@router.get("/weekly", response_model=WeeklyHoroscopeResponse)
def get_weekly_horoscope(
    request: Request,
    current_user: User = Depends(get_premium_user),
    session: Session = Depends(get_session),
):
    """
    Return an AI-generated weekly horoscope for the user's zodiac sign.
    Premium only.
    """
    today = datetime.now(timezone.utc).date()
    # Start of the current week (Monday)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    lang = current_user.preferred_language
    zodiac = current_user.zodiac_sign or "Aries"

    if lang == "en":
        prompt_date = f"the week of {week_start.isoformat()} to {week_end.isoformat()}"
    else:
        prompt_date = f"la semana del {week_start.isoformat()} al {week_end.isoformat()}"

    horoscope = generate_daily_horoscope(
        zodiac_sign=zodiac,
        current_date=prompt_date,
        language=lang,
        onboarding_answers=current_user.onboarding_answers,
    )

    return WeeklyHoroscopeResponse(
        zodiac_sign=zodiac,
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        horoscope=horoscope,
        language=lang,
    )
