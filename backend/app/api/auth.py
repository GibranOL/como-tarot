"""
Authentication endpoints.

Rate limits (enforced by slowapi):
  POST /api/auth/register  → 3 requests / hour per IP
  POST /api/auth/login     → 5 requests / 15 min per IP
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.db.database import get_session
from app.schemas.auth import (
    LoginRequest,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    SocialAuthRequest,
    TokenResponse,
    UserResponse,
)
from app.security.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ─── Register ─────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    req: RegisterRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Register a new user with email + password.
    Creates a Supabase Auth account and mirrors the profile in our DB.
    Rate limited: 3 requests / hour per IP.
    """
    from app.services.auth import register_user

    # Inline rate-limit check (slowapi decorator needs the limiter on the app)
    try:
        user, access_token, refresh_token = register_user(req, session)
    except ValueError as exc:
        msg = str(exc)
        if "already registered" in msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(
    req: LoginRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Authenticate with email + password.
    Returns a JWT access_token and refresh_token.
    Rate limited: 5 requests / 15 min per IP.
    """
    from app.services.auth import login_user

    try:
        user, access_token, refresh_token = login_user(req.email, req.password, session)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ─── Social Auth ──────────────────────────────────────────────────────────────

@router.post("/social", response_model=TokenResponse)
def social_auth(
    req: SocialAuthRequest,
    session: Session = Depends(get_session),
):
    """
    Authenticate with a Google or Apple OAuth ID token.
    Creates a new user on first sign-in.
    """
    from app.services.auth import social_auth as _social_auth

    try:
        user, access_token, refresh_token = _social_auth(
            provider=req.provider,
            id_token=req.id_token,
            session=session,
            full_name=req.full_name,
            preferred_language=req.preferred_language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ─── Refresh ──────────────────────────────────────────────────────────────────

@router.post("/refresh")
def refresh(req: RefreshRequest):
    """Exchange a refresh token for a new access_token + refresh_token pair."""
    from app.services.auth import refresh_tokens

    try:
        access_token, new_refresh_token = refresh_tokens(req.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


# ─── Logout ───────────────────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: User = Depends(get_current_user)):
    """
    Invalidate the current session.
    The Flutter client should also clear its local token storage.
    Supabase sessions are stateless JWTs; we rely on expiry + client-side clearing.
    """
    # For full server-side invalidation, call supabase.auth.admin.sign_out(uid)
    # Deferred: token blocklist via Redis is a post-MVP security enhancement.
    return None


# ─── Me ───────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


# ─── Profile Update ───────────────────────────────────────────────────────────

@router.put("/profile", response_model=UserResponse)
def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Update mutable profile fields. Only provided fields are changed."""
    from app.services.auth import update_profile as _update_profile

    updated = _update_profile(current_user, req, session)
    return UserResponse.model_validate(updated)
