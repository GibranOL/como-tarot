"""
FastAPI dependencies for authentication.
get_current_user: validates the Supabase JWT on every protected request.
"""
import uuid
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from supabase import create_client, AuthApiError

from app.config import settings
from app.db.database import get_session
from app.models.user import User

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: Session = Depends(get_session),
) -> User:
    """
    Validate the Bearer JWT with Supabase, then load the User from our DB.

    Raises 401 if:
    - Token is missing / malformed
    - Token is expired or invalid (Supabase rejects it)
    - No matching user in our DB (shouldn't happen normally)
    """
    token = credentials.credentials

    # 1. Validate JWT with Supabase (signature + expiry)
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    try:
        user_response = supabase.auth.get_user(token)
    except AuthApiError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    supabase_uid = uuid.UUID(user_response.user.id)

    # 2. Load user profile from our DB
    user = session.get(User, supabase_uid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_premium_user(current_user: User = Depends(get_current_user)) -> User:
    """Like get_current_user but also asserts the user is on a premium plan."""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires a premium subscription",
        )
    return current_user
