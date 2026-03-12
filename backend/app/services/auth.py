"""
Authentication service — wraps Supabase Auth and our users table.
Supabase handles: password hashing, JWT issuance, OAuth, email verification.
We handle: user profile in our DB, business rules, zodiac/life-number calculation.
"""
import uuid
import logging
from datetime import datetime, timezone

from sqlmodel import Session, select
from supabase import create_client, Client, AuthApiError

from app.config import settings
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.auth import RegisterRequest, ProfileUpdateRequest

logger = logging.getLogger(__name__)


def _get_supabase() -> Client:
    """Return a Supabase client using the service-role key for backend operations."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


# ─── Registration ─────────────────────────────────────────────────────────────

def register_user(req: RegisterRequest, session: Session) -> tuple[User, str, str]:
    """
    1. Create the user in Supabase Auth.
    2. Mirror the profile in our users table (using Supabase's UUID as PK).
    3. Create a free subscription record.
    Returns (user, access_token, refresh_token).
    Raises ValueError on duplicate email or Supabase error.
    """
    from app.services.astrology import get_zodiac_sign
    from app.services.numerology import calculate_life_number

    supabase = _get_supabase()

    # Step 1: Create Supabase Auth user
    try:
        auth_response = supabase.auth.admin.create_user({
            "email": req.email,
            "password": req.password,
            "email_confirm": True,   # skip email verification in dev; toggle for prod
        })
    except AuthApiError as exc:
        if "already registered" in str(exc).lower() or "already been registered" in str(exc).lower():
            raise ValueError("Email already registered") from exc
        raise ValueError(f"Supabase auth error: {exc}") from exc

    supabase_uid = uuid.UUID(auth_response.user.id)

    # Step 2: Sign in to get a real session (admin.create_user doesn't return one)
    try:
        session_response = supabase.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password,
        })
        access_token = session_response.session.access_token
        refresh_token = session_response.session.refresh_token
    except AuthApiError as exc:
        raise ValueError(f"Could not create session after registration: {exc}") from exc

    # Step 3: Create profile in our DB
    user = User(
        id=supabase_uid,
        email=req.email,
        full_name=req.full_name.strip(),
        auth_provider="email",
        birth_date=req.birth_date,
        birth_time=req.birth_time,
        birth_city=req.birth_city,
        birth_country=req.birth_country,
        preferred_language=req.preferred_language,
        timezone=req.timezone,
        onboarding_answers=req.onboarding_answers,
        zodiac_sign=get_zodiac_sign(req.birth_date),
        life_number=calculate_life_number(req.birth_date),
    )
    session.add(user)
    session.flush()  # Ensure user row exists before FK reference

    # Step 4: Create free subscription
    subscription = Subscription(user_id=supabase_uid, plan="free")
    session.add(subscription)

    session.commit()
    session.refresh(user)
    return user, access_token, refresh_token


# ─── Login ────────────────────────────────────────────────────────────────────

def login_user(email: str, password: str, session: Session) -> tuple[User, str, str]:
    """
    Authenticate via Supabase, then fetch our User profile.
    Returns (user, access_token, refresh_token).
    Raises ValueError on wrong credentials or user not found in our DB.
    """
    supabase = _get_supabase()

    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
    except AuthApiError as exc:
        raise ValueError("Invalid email or password") from exc

    supabase_uid = uuid.UUID(auth_response.user.id)
    user = session.get(User, supabase_uid)
    if user is None:
        raise ValueError("User profile not found — contact support")

    access_token = auth_response.session.access_token
    refresh_token = auth_response.session.refresh_token
    return user, access_token, refresh_token


# ─── Social Auth ──────────────────────────────────────────────────────────────

def social_auth(provider: str, id_token: str, session: Session, full_name: str | None, preferred_language: str) -> tuple[User, str, str]:
    """
    Validate a Google or Apple ID token with Supabase, then upsert our User.
    Returns (user, access_token, refresh_token).
    """
    from app.services.astrology import get_zodiac_sign
    from app.services.numerology import calculate_life_number

    supabase = _get_supabase()

    try:
        auth_response = supabase.auth.sign_in_with_id_token({
            "provider": provider,
            "token": id_token,
        })
    except AuthApiError as exc:
        raise ValueError(f"Social auth failed: {exc}") from exc

    supabase_uid = uuid.UUID(auth_response.user.id)
    access_token = auth_response.session.access_token
    refresh_token = auth_response.session.refresh_token

    # Upsert profile
    user = session.get(User, supabase_uid)
    if user is None:
        email = auth_response.user.email or ""
        name = full_name or (auth_response.user.user_metadata or {}).get("full_name", "")
        user = User(
            id=supabase_uid,
            email=email,
            full_name=name or email.split("@")[0],
            auth_provider=provider,
            birth_date=datetime.now(timezone.utc).date(),  # placeholder — user updates in profile
            preferred_language=preferred_language,
        )
        session.add(user)
        session.add(Subscription(user_id=supabase_uid, plan="free"))
        session.commit()
        session.refresh(user)

    return user, access_token, refresh_token


# ─── Token Refresh ────────────────────────────────────────────────────────────

def refresh_tokens(refresh_token: str) -> tuple[str, str]:
    """Exchange a refresh token for a new access token pair."""
    supabase = _get_supabase()
    try:
        response = supabase.auth.refresh_session(refresh_token)
        return response.session.access_token, response.session.refresh_token
    except AuthApiError as exc:
        raise ValueError("Invalid or expired refresh token") from exc


# ─── Profile Update ───────────────────────────────────────────────────────────

def update_profile(user: User, req: ProfileUpdateRequest, session: Session) -> User:
    """Apply non-null fields from req onto the user record."""
    data = req.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(user, field, value)
    user.updated_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_user_by_id(user_id: uuid.UUID, session: Session) -> User | None:
    return session.get(User, user_id)
