"""
Tarot endpoints.

GET  /api/tarot/daily     → Get (or create) today's 3-card reading
POST /api/tarot/ask       → Ask the AI tarotist a free-form question
GET  /api/tarot/history   → Past readings (free: 7 days, premium: all)

Rate limits:
  GET  /api/tarot/daily  → 30 req/hr per user
  POST /api/tarot/ask    → 10 req/hr per user
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, select, func

from app.db.database import get_session
from app.models.reading import DailyReading, TarotistQuestion
from app.models.user import User
from app.schemas.tarot import (
    AskTarotistRequest,
    DailyReadingResponse,
    ReadingHistoryResponse,
    TarotistAnswerResponse,
)
from app.security.dependencies import get_current_user
from app.security.sanitizer import sanitize_input, SanitizationError
from app.services.ai import generate_tarot_interpretation, answer_tarotist_question
from app.services.limits import check_user_limits
from app.services.tarot import draw_cards

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tarot", tags=["tarot"])


# ── Daily Reading ─────────────────────────────────────────────────────────────

@router.get("/daily", response_model=DailyReadingResponse)
def get_daily_reading(
    request: Request,
    spread_type: str = Query(default="past_present_future"),
    language: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Return today's 3-card reading for the authenticated user.

    If a reading already exists for today (UTC date), it is returned from the
    database — no new AI call is made (caching the daily reading saves Gemini quota).
    If no reading exists, cards are drawn, AI interpretation is generated, and the
    result is persisted.

    Free users: 1 reading per day. Premium users: unlimited.
    """
    lang = language or current_user.preferred_language
    today = datetime.now(timezone.utc).date()

    # Return cached reading if it exists for today
    existing = session.exec(
        select(DailyReading).where(
            DailyReading.user_id == current_user.id,
            DailyReading.reading_date == today,
        )
    ).first()
    if existing:
        return existing

    # Check free-tier limits
    limits = check_user_limits(session, current_user)
    if not limits["can_read"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily reading limit reached. Upgrade to Premium for unlimited readings.",
        )

    # Validate spread type
    allowed_spreads = ("past_present_future", "situation_action_outcome")
    if spread_type not in allowed_spreads:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"spread_type must be one of {allowed_spreads}",
        )

    # Draw cards and generate AI interpretation
    cards = draw_cards(3, spread_type=spread_type)  # type: ignore[arg-type]
    interpretation = generate_tarot_interpretation(
        cards=cards,
        spread_type=spread_type,
        question=None,
        zodiac_sign=current_user.zodiac_sign or "Unknown",
        language=lang,
        onboarding_answers=current_user.onboarding_answers,
    )

    reading = DailyReading(
        user_id=current_user.id,
        reading_date=today,
        cards_drawn=cards,
        ai_interpretation=interpretation,
        spread_type=spread_type,
        language=lang,
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)

    logger.info("Created daily reading for user %s", current_user.id)
    return reading


# ── Ask the Tarotist ──────────────────────────────────────────────────────────

@router.post("/ask", response_model=TarotistAnswerResponse, status_code=status.HTTP_201_CREATED)
def ask_tarotist(
    req: AskTarotistRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Submit a free-form question to the AI tarotist.

    Free users: 1 question per day.
    Premium users: unlimited.
    The question is sanitized before being sent to Gemini.
    """
    lang = req.language or current_user.preferred_language

    # Sanitize before any processing — blocks XSS and prompt injection (CLAUDE.md Layer 3)
    try:
        clean_question = sanitize_input(req.question)
    except SanitizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    limits = check_user_limits(session, current_user)
    if not limits["can_ask"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily question limit reached. Upgrade to Premium for unlimited questions.",
        )

    answer = answer_tarotist_question(
        question=clean_question,
        zodiac_sign=current_user.zodiac_sign or "Unknown",
        language=lang,
        onboarding_answers=current_user.onboarding_answers,
    )

    record = TarotistQuestion(
        user_id=current_user.id,
        question=clean_question,
        answer=answer,
        is_free=not current_user.is_premium,
        language=lang,
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    return record


# ── Reading History ───────────────────────────────────────────────────────────

@router.get("/history", response_model=ReadingHistoryResponse)
def get_reading_history(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Return the user's past daily readings.

    Free users: last 7 days only.
    Premium users: full history, paginated.
    """
    from datetime import timedelta

    query = select(DailyReading).where(DailyReading.user_id == current_user.id)

    if not current_user.is_premium:
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=7)
        query = query.where(DailyReading.reading_date >= cutoff)

    count_stmt = select(func.count()).select_from(
        query.subquery()
    )
    total = session.exec(count_stmt).one()

    readings = session.exec(
        query.order_by(DailyReading.reading_date.desc())  # type: ignore[attr-defined]
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return ReadingHistoryResponse(
        readings=list(readings),
        total=total,
        page=page,
        page_size=page_size,
    )
