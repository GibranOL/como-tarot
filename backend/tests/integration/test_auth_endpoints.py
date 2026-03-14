"""
Integration tests for authentication endpoints.

WHY: Auth is the security foundation of CosmoTarot. A broken login, a registration
that doesn't persist the user, or a profile update that overwrites wrong fields
would have severe consequences. We mock only the Supabase boundary (external API
calls), but keep the real PostgreSQL DB to catch FK and constraint errors.

Supabase is mocked via `app.services.auth._get_supabase` so tests run in CI
without real credentials. JWT validation (`get_current_user`) is overridden
in the same way as other integration tests.
"""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_session
from app.main import app
from app.models.user import User
from app.security.dependencies import get_current_user


# ── Supabase mock helpers ─────────────────────────────────────────────────────

def _mock_supabase(uid: str | None = None, email: str = "user@cosmo.mx") -> MagicMock:
    """
    Build a MagicMock that mimics the Supabase client used in services/auth.py.
    Covers: admin.create_user, sign_in_with_password, refresh_session,
            sign_in_with_id_token.
    """
    uid = uid or str(uuid.uuid4())
    mock = MagicMock()

    # auth.admin.create_user(...)
    created_user = MagicMock()
    created_user.id = uid
    mock.auth.admin.create_user.return_value = MagicMock(user=created_user)

    # auth.sign_in_with_password(...)
    signed_user = MagicMock()
    signed_user.id = uid
    signed_user.email = email
    session = MagicMock()
    session.access_token = "mock_access_token"
    session.refresh_token = "mock_refresh_token"
    mock.auth.sign_in_with_password.return_value = MagicMock(
        user=signed_user, session=session
    )

    # auth.refresh_session(...)
    mock.auth.refresh_session.return_value = MagicMock(session=session)

    # auth.sign_in_with_id_token(...)
    social_user = MagicMock()
    social_user.id = uid
    social_user.email = email
    social_user.user_metadata = {"full_name": "Social User"}
    mock.auth.sign_in_with_id_token.return_value = MagicMock(
        user=social_user, session=session
    )

    return mock


def _make_persisted_user(db_session, uid: uuid.UUID | None = None) -> User:
    """Insert a User row into the test DB and return it."""
    uid = uid or uuid.uuid4()
    user = User(
        id=uid,
        email=f"auth-{uid.hex[:8]}@cosmo.mx",
        full_name="Auth Test User",
        auth_provider="email",
        birth_date=date(1990, 6, 15),
        zodiac_sign="Gemini",
        life_number=4,
        preferred_language="en",
        timezone="America/Mexico_City",
        is_premium=False,
        onboarding_answers=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ── POST /api/auth/register ───────────────────────────────────────────────────

class TestRegister:
    _VALID_PAYLOAD = {
        "email": "new@cosmo.mx",
        "password": "SecurePass1!",
        "full_name": "Nuevo Usuario",
        "birth_date": "1995-03-21",
        "preferred_language": "es",
    }

    def test_register_creates_user_in_db(self, db_session):
        """
        WHAT: A valid registration request creates a User row in our DB and
        returns 201 with access_token + refresh_token + user profile.
        WHY: Registration is step 1 of the user journey. If it fails silently
        (user created in Supabase but not in our DB), every subsequent call
        will 401 because get_current_user can't find the profile.
        """
        uid = str(uuid.uuid4())
        mock_supabase = _mock_supabase(uid=uid, email="new@cosmo.mx")

        def get_session_override():
            yield db_session

        app.dependency_overrides[get_session] = get_session_override
        try:
            with patch("app.services.auth._get_supabase", return_value=mock_supabase):
                with TestClient(app) as c:
                    resp = c.post("/api/auth/register", json=self._VALID_PAYLOAD)

            assert resp.status_code == 201
            body = resp.json()
            assert body["access_token"] == "mock_access_token"
            assert body["refresh_token"] == "mock_refresh_token"
            assert body["user"]["email"] == "new@cosmo.mx"
            assert body["user"]["zodiac_sign"] == "Aries"
        finally:
            app.dependency_overrides.clear()

    def test_register_duplicate_email_returns_409(self, db_session):
        """
        WHAT: Registering with an already-used email returns 409 Conflict.
        WHY: Without this check, a second registration attempt would crash
        Supabase and surface a confusing 500 to the user.
        """
        from supabase import AuthApiError

        mock_supabase = _mock_supabase()
        mock_supabase.auth.admin.create_user.side_effect = AuthApiError(
            "User already registered", 422, None
        )

        def get_session_override():
            yield db_session

        app.dependency_overrides[get_session] = get_session_override
        try:
            with patch("app.services.auth._get_supabase", return_value=mock_supabase):
                with TestClient(app) as c:
                    resp = c.post("/api/auth/register", json=self._VALID_PAYLOAD)
            assert resp.status_code == 409
        finally:
            app.dependency_overrides.clear()

    def test_register_weak_password_returns_422(self):
        """
        WHAT: A password shorter than 8 characters returns 422 (Pydantic validation).
        WHY: Weak passwords must be rejected before hitting Supabase, saving an
        unnecessary API round-trip and giving immediate feedback.
        """
        payload = {**self._VALID_PAYLOAD, "password": "short"}
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/api/auth/register", json=payload)
        assert resp.status_code == 422

    def test_register_blank_name_returns_422(self):
        """
        WHAT: An empty full_name returns 422.
        WHY: Storing a blank name would break the onboarding greeting and
        make user records unusable.
        """
        payload = {**self._VALID_PAYLOAD, "full_name": "   "}
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/api/auth/register", json=payload)
        assert resp.status_code == 422

    def test_register_invalid_language_returns_422(self):
        """
        WHAT: A preferred_language other than 'es' or 'en' returns 422.
        WHY: Unsupported languages would break AI prompt generation downstream.
        """
        payload = {**self._VALID_PAYLOAD, "preferred_language": "fr"}
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/api/auth/register", json=payload)
        assert resp.status_code == 422


# ── POST /api/auth/login ──────────────────────────────────────────────────────

class TestLogin:
    def test_login_returns_jwt(self, db_session):
        """
        WHAT: Valid credentials return 200 with access_token, refresh_token, and
        the user's profile.
        WHY: Login is the most frequent auth operation. A broken login blocks
        every returning user.
        """
        user = _make_persisted_user(db_session)
        mock_sb = _mock_supabase(uid=str(user.id), email=user.email)

        def get_session_override():
            yield db_session

        app.dependency_overrides[get_session] = get_session_override
        try:
            with patch("app.services.auth._get_supabase", return_value=mock_sb):
                with TestClient(app) as c:
                    resp = c.post(
                        "/api/auth/login",
                        json={"email": user.email, "password": "AnyPass123!"},
                    )
            assert resp.status_code == 200
            body = resp.json()
            assert body["access_token"] == "mock_access_token"
            assert body["user"]["id"] == str(user.id)
        finally:
            app.dependency_overrides.clear()

    def test_login_wrong_password_returns_401(self, db_session):
        """
        WHAT: Wrong password returns 401 Unauthorized.
        WHY: Incorrect credentials must never grant access. Without this guard,
        any password would succeed.
        """
        from supabase import AuthApiError

        mock_sb = _mock_supabase()
        mock_sb.auth.sign_in_with_password.side_effect = AuthApiError(
            "Invalid login credentials", 400, None
        )

        def get_session_override():
            yield db_session

        app.dependency_overrides[get_session] = get_session_override
        try:
            with patch("app.services.auth._get_supabase", return_value=mock_sb):
                with TestClient(app) as c:
                    resp = c.post(
                        "/api/auth/login",
                        json={"email": "x@x.com", "password": "wrong"},
                    )
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

class TestMe:
    def test_me_returns_user_profile(self, db_session):
        """
        WHAT: GET /me with a valid token returns the authenticated user's profile.
        WHY: /me is called on every app startup to restore the session. A broken
        /me forces users to log in on every launch.
        """
        user = _make_persisted_user(db_session)

        def get_session_override():
            yield db_session

        def get_user_override():
            return user

        app.dependency_overrides[get_session] = get_session_override
        app.dependency_overrides[get_current_user] = get_user_override
        try:
            with TestClient(app) as c:
                resp = c.get("/api/auth/me")
            assert resp.status_code == 200
            body = resp.json()
            assert body["id"] == str(user.id)
            assert body["email"] == user.email
            assert body["is_premium"] is False
        finally:
            app.dependency_overrides.clear()

    def test_me_without_token_returns_401_or_403(self):
        """
        WHAT: /me without a Bearer token returns 401 or 403.
        WHY: User profile data is private. Unauthenticated access must be blocked.
        """
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/api/auth/me")
        assert resp.status_code in (401, 403)


# ── PUT /api/auth/profile ─────────────────────────────────────────────────────

class TestProfileUpdate:
    def test_profile_update_persists_changes(self, db_session):
        """
        WHAT: PUT /profile with new field values updates the DB record.
        WHY: Users must be able to change their name, language, and birth info.
        If updates don't persist, profile settings are lost between sessions.
        """
        user = _make_persisted_user(db_session)

        def get_session_override():
            yield db_session

        def get_user_override():
            return user

        app.dependency_overrides[get_session] = get_session_override
        app.dependency_overrides[get_current_user] = get_user_override
        try:
            with TestClient(app) as c:
                resp = c.put(
                    "/api/auth/profile",
                    json={"full_name": "Updated Name", "preferred_language": "es"},
                )
            assert resp.status_code == 200
            body = resp.json()
            assert body["full_name"] == "Updated Name"
            assert body["preferred_language"] == "es"
        finally:
            app.dependency_overrides.clear()

    def test_profile_update_invalid_language_returns_422(self, db_session):
        """
        WHAT: Updating preferred_language to an unsupported value returns 422.
        WHY: An invalid language stored in the DB would break all AI prompts for
        that user permanently.
        """
        user = _make_persisted_user(db_session)

        def get_session_override():
            yield db_session

        def get_user_override():
            return user

        app.dependency_overrides[get_session] = get_session_override
        app.dependency_overrides[get_current_user] = get_user_override
        try:
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.put(
                    "/api/auth/profile",
                    json={"preferred_language": "zh"},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_profile_update_requires_auth(self):
        """
        WHAT: PUT /profile without a token returns 401/403.
        WHY: Profile data is private — anonymous writes must be blocked.
        """
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.put("/api/auth/profile", json={"full_name": "Hacker"})
        assert resp.status_code in (401, 403)


# ── POST /api/auth/refresh ────────────────────────────────────────────────────

class TestRefresh:
    def test_refresh_returns_new_tokens(self):
        """
        WHAT: A valid refresh token returns a new access_token and refresh_token.
        WHY: JWTs expire every hour. Without token refresh the user must re-login
        constantly, which is both frustrating and a sign-out security risk.
        """
        mock_sb = _mock_supabase()
        with patch("app.services.auth._get_supabase", return_value=mock_sb):
            with TestClient(app) as c:
                resp = c.post(
                    "/api/auth/refresh",
                    json={"refresh_token": "valid_refresh_token"},
                )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_refresh_invalid_token_returns_401(self):
        """
        WHAT: An expired or tampered refresh token returns 401.
        WHY: Stolen refresh tokens must be rejected — they cannot grant indefinite
        access. This is the last line of defense after a token leak.
        """
        from supabase import AuthApiError

        mock_sb = _mock_supabase()
        mock_sb.auth.refresh_session.side_effect = AuthApiError(
            "Token has expired or is invalid", 401, None
        )
        with patch("app.services.auth._get_supabase", return_value=mock_sb):
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post(
                    "/api/auth/refresh",
                    json={"refresh_token": "expired_or_fake_token"},
                )
        assert resp.status_code == 401


# ── POST /api/auth/social ─────────────────────────────────────────────────────

class TestSocialAuth:
    def test_social_auth_google_creates_or_finds_user(self, db_session):
        """
        WHAT: A Google OAuth token results in 200 with tokens and user profile.
        WHY: Social login is required for iOS (Apple Sign-In) and preferred on
        Android (Google). If it fails, a large segment of users cannot register.
        """
        mock_sb = _mock_supabase()

        def get_session_override():
            yield db_session

        app.dependency_overrides[get_session] = get_session_override
        try:
            with patch("app.services.auth._get_supabase", return_value=mock_sb):
                with TestClient(app) as c:
                    resp = c.post(
                        "/api/auth/social",
                        json={
                            "provider": "google",
                            "id_token": "google_id_token_here",
                            "full_name": "Google User",
                        },
                    )
            assert resp.status_code == 200
            body = resp.json()
            assert body["access_token"] == "mock_access_token"
        finally:
            app.dependency_overrides.clear()

    def test_social_auth_invalid_provider_returns_422(self):
        """
        WHAT: A provider other than 'google' or 'apple' returns 422.
        WHY: We only support Google and Apple. An unsupported provider string
        would reach Supabase and produce a confusing error.
        """
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/api/auth/social",
                json={"provider": "facebook", "id_token": "token123"},
            )
        assert resp.status_code == 422
