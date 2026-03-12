"""
Numerology endpoints.

GET /api/numerology/profile → Life number + personal year + personal month
"""
import logging

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.db.database import get_session
from app.models.user import User
from app.schemas.horoscope import NumerologyProfileResponse, NumberInfoResponse
from app.security.dependencies import get_current_user
from app.services.numerology import get_full_numerology_profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/numerology", tags=["numerology"])


@router.get("/profile", response_model=NumerologyProfileResponse)
def get_numerology_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Return the complete numerology profile for the authenticated user.

    Includes:
    - Life path number (calculated once from birth date)
    - Personal year number (changes annually)
    - Personal month number (changes monthly)
    - Full meaning data for the life path number

    Available to free and premium users.
    """
    profile = get_full_numerology_profile(current_user.birth_date)

    info = profile["life_number_info"]
    info_response = NumberInfoResponse(**info) if info else None

    return NumerologyProfileResponse(
        life_number=profile["life_number"],
        personal_year=profile["personal_year"],
        personal_month=profile["personal_month"],
        life_number_info=info_response,
        birth_date=current_user.birth_date,
    )
