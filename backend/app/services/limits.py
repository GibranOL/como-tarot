"""
Usage limits service — enforces free-tier daily quotas.

Free tier limits (reset at midnight user local time, approximated as UTC midnight):
  - 1 daily tarot reading per day
  - 1 tarotist question per day

Premium users have no limits.
"""
import uuid
from datetime import date, datetime, timezone

from sqlmodel import Session, select, func

from app.models.reading import DailyReading, TarotistQuestion
from app.models.user import User


# ── Free-tier daily caps ──────────────────────────────────────────────────────
FREE_DAILY_READINGS = 1
FREE_DAILY_QUESTIONS = 1


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def get_readings_today(session: Session, user_id: uuid.UUID) -> int:
    """Count how many daily readings the user has created today (UTC date)."""
    today = _today_utc()
    statement = (
        select(func.count())
        .select_from(DailyReading)
        .where(DailyReading.user_id == user_id, DailyReading.reading_date == today)
    )
    return session.exec(statement).one()


def get_questions_today(session: Session, user_id: uuid.UUID) -> int:
    """Count how many tarotist questions the user has asked today (UTC date)."""
    today = _today_utc()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    statement = (
        select(func.count())
        .select_from(TarotistQuestion)
        .where(
            TarotistQuestion.user_id == user_id,
            TarotistQuestion.asked_at >= today_start,
        )
    )
    return session.exec(statement).one()


def check_user_limits(session: Session, user: User) -> dict:
    """
    Return a dict describing what the user can and cannot do right now.

    {
        "is_premium": bool,
        "can_read": bool,
        "can_ask": bool,
        "readings_today": int,
        "questions_today": int,
        "daily_reading_limit": int | None,   # None = unlimited
        "daily_question_limit": int | None,  # None = unlimited
    }
    """
    readings_today = get_readings_today(session, user.id)
    questions_today = get_questions_today(session, user.id)

    if user.is_premium:
        return {
            "is_premium": True,
            "can_read": True,
            "can_ask": True,
            "readings_today": readings_today,
            "questions_today": questions_today,
            "daily_reading_limit": None,
            "daily_question_limit": None,
        }

    return {
        "is_premium": False,
        "can_read": readings_today < FREE_DAILY_READINGS,
        "can_ask": questions_today < FREE_DAILY_QUESTIONS,
        "readings_today": readings_today,
        "questions_today": questions_today,
        "daily_reading_limit": FREE_DAILY_READINGS,
        "daily_question_limit": FREE_DAILY_QUESTIONS,
    }
