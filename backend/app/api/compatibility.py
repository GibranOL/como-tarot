"""
Compatibility endpoints.

POST /api/compatibility/check   → Check compatibility with a partner's sign (premium)
GET  /api/compatibility/history → Past compatibility readings (premium)

Rate limit:
  POST /api/compatibility/check → 5 req/hr per user
"""
import logging

from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session, select, func

from app.db.database import get_session
from app.models.compatibility import CompatibilityReading
from app.models.user import User
from app.schemas.tarot import (
    CompatibilityCheckRequest,
    CompatibilityHistoryResponse,
    CompatibilityResponse,
)
from app.security.dependencies import get_premium_user
from app.services.ai import generate_compatibility_analysis
from app.services.astrology import calculate_compatibility

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compatibility", tags=["compatibility"])


# ── Check Compatibility ───────────────────────────────────────────────────────

@router.post(
    "/check",
    response_model=CompatibilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def check_compatibility(
    req: CompatibilityCheckRequest,
    request: Request,
    current_user: User = Depends(get_premium_user),
    session: Session = Depends(get_session),
):
    """
    Calculate and narrate compatibility between the user's zodiac sign
    and a partner's sign. Premium only.

    Returns a compatibility score (1–100), level, and AI-generated narrative.
    """
    lang = req.language or current_user.preferred_language
    user_sign = current_user.zodiac_sign or "Aries"
    partner_sign = req.partner_zodiac

    # Calculate numeric compatibility
    compat = calculate_compatibility(user_sign, partner_sign)

    # Generate AI narrative
    ai_text = generate_compatibility_analysis(
        sign_a=user_sign,
        sign_b=partner_sign,
        score=compat["score"],
        level=compat["level"],
        element_a=compat["element_a"],
        element_b=compat["element_b"],
        language=lang,
        onboarding_answers=current_user.onboarding_answers,
    )

    record = CompatibilityReading(
        user_id=current_user.id,
        partner_zodiac=partner_sign,
        partner_birth_date=req.partner_birth_date,
        ai_interpretation=ai_text,
        compatibility_score=compat["score"],
        language=lang,
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    logger.info(
        "Compatibility check: %s ↔ %s = %d (%s) for user %s",
        user_sign, partner_sign, compat["score"], compat["level"], current_user.id,
    )
    return record


# ── Compatibility History ─────────────────────────────────────────────────────

@router.get("/history", response_model=CompatibilityHistoryResponse)
def get_compatibility_history(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_premium_user),
    session: Session = Depends(get_session),
):
    """
    Return past compatibility readings for the authenticated user.
    Premium only. Paginated.
    """
    query = select(CompatibilityReading).where(
        CompatibilityReading.user_id == current_user.id
    )

    count_stmt = select(func.count()).select_from(query.subquery())
    total = session.exec(count_stmt).one()

    readings = session.exec(
        query.order_by(CompatibilityReading.created_at.desc())  # type: ignore[attr-defined]
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return CompatibilityHistoryResponse(
        readings=list(readings),
        total=total,
    )
