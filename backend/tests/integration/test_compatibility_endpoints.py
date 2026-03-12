"""
Integration tests for compatibility endpoints.

WHY: Compatibility is a premium feature and a key revenue differentiator.
Getting the score wrong or failing to gate it would directly impact revenue
and user trust.
"""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db.database import get_session
from app.main import app
from app.models.user import User
from app.security.dependencies import get_current_user, get_premium_user


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(name="test_engine", scope="module")
def test_engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="db_session")
def db_session_fixture(test_engine):
    with Session(test_engine) as session:
        yield session


def _make_user(is_premium: bool = False) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"compat-{'prem' if is_premium else 'free'}@cosmo.mx",
        full_name="Compat User",
        auth_provider="email",
        birth_date=date(1990, 7, 25),
        zodiac_sign="Leo",
        life_number=6,
        preferred_language="en",
        timezone="America/Mexico_City",
        is_premium=is_premium,
        onboarding_answers=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture(name="free_client")
def free_client_fixture(db_session):
    user = _make_user(is_premium=False)

    app.dependency_overrides[get_session] = lambda: (yield db_session)
    app.dependency_overrides[get_current_user] = lambda: user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="premium_client")
def premium_client_fixture(db_session):
    user = _make_user(is_premium=True)

    app.dependency_overrides[get_session] = lambda: (yield db_session)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_premium_user] = lambda: user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


_AI_COMPAT = "Leo and Aries share a blazing fire connection — passionate and dynamic."


# ── POST /api/compatibility/check ─────────────────────────────────────────────

class TestCompatibilityCheck:
    def test_check_compatibility_returns_score(self, premium_client):
        """
        WHAT: Premium user submits a partner zodiac and receives a score + AI narrative.
        WHY: This is the core of the compatibility feature — must return valid data.
        """
        with patch("app.api.compatibility.generate_compatibility_analysis", return_value=_AI_COMPAT):
            resp = premium_client.post(
                "/api/compatibility/check",
                json={"partner_zodiac": "Aries"},
            )
        assert resp.status_code == 201
        body = resp.json()
        assert body["partner_zodiac"] == "Aries"
        assert 1 <= body["compatibility_score"] <= 100
        assert body["ai_interpretation"] == _AI_COMPAT

    def test_check_compatibility_requires_premium(self, free_client):
        """
        WHAT: A free user gets 403 when attempting a compatibility check.
        WHY: This is a premium-only feature — the server must enforce the gate,
        not just the UI.
        """
        resp = free_client.post(
            "/api/compatibility/check",
            json={"partner_zodiac": "Aries"},
        )
        assert resp.status_code == 403

    def test_check_compatibility_with_invalid_sign(self, premium_client):
        """
        WHAT: An invalid zodiac sign name returns 422 validation error.
        WHY: We must not let garbage signs reach the astrology service.
        """
        resp = premium_client.post(
            "/api/compatibility/check",
            json={"partner_zodiac": "NotASign"},
        )
        assert resp.status_code == 422

    def test_check_compatibility_requires_auth(self):
        """WHAT: Unauthenticated request returns 401/403."""
        with TestClient(app, raise_server_exceptions=False) as raw:
            resp = raw.post("/api/compatibility/check", json={"partner_zodiac": "Aries"})
        assert resp.status_code in (401, 403)

    def test_check_compatibility_with_partner_birth_date(self, premium_client):
        """
        WHAT: Optional partner_birth_date is accepted and stored without error.
        WHY: The frontend sends birth date when the user provides it — must not crash.
        """
        with patch("app.api.compatibility.generate_compatibility_analysis", return_value=_AI_COMPAT):
            resp = premium_client.post(
                "/api/compatibility/check",
                json={"partner_zodiac": "Scorpio", "partner_birth_date": "1992-11-05"},
            )
        assert resp.status_code == 201


# ── GET /api/compatibility/history ───────────────────────────────────────────

class TestCompatibilityHistory:
    def test_history_returns_list(self, premium_client):
        """
        WHAT: /history returns a paginated list of past compatibility readings.
        WHY: Users should be able to review who they've checked compatibility with.
        """
        with patch("app.api.compatibility.generate_compatibility_analysis", return_value=_AI_COMPAT):
            premium_client.post(
                "/api/compatibility/check",
                json={"partner_zodiac": "Taurus"},
            )

        resp = premium_client.get("/api/compatibility/history")
        assert resp.status_code == 200
        body = resp.json()
        assert "readings" in body
        assert "total" in body
        assert isinstance(body["readings"], list)

    def test_history_requires_premium(self, free_client):
        """WHAT: Free user gets 403 on compatibility history."""
        resp = free_client.get("/api/compatibility/history")
        assert resp.status_code == 403
