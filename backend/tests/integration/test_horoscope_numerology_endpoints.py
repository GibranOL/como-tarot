"""
Integration tests for horoscope and numerology endpoints.

WHY: These endpoints are visible to every user on the home screen. A broken
horoscope or wrong life number would be the first thing users see — must be
solid before shipping.
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


def _make_user(is_premium: bool = False, lang: str = "en") -> User:
    return User(
        id=uuid.uuid4(),
        email=f"test-{'prem' if is_premium else 'free'}@cosmo.mx",
        full_name="Test User",
        auth_provider="email",
        birth_date=date(1990, 7, 25),
        zodiac_sign="Leo",
        life_number=6,
        preferred_language=lang,
        timezone="America/Mexico_City",
        is_premium=is_premium,
        onboarding_answers=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture(name="free_client")
def free_client_fixture(db_session):
    user = _make_user(is_premium=False)

    def get_session_override():
        yield db_session

    def get_user_override():
        return user

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_user_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="premium_client")
def premium_client_fixture(db_session):
    user = _make_user(is_premium=True)

    def get_session_override():
        yield db_session

    def get_user_override():
        return user

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_user_override
    app.dependency_overrides[get_premium_user] = get_user_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


_HOROSCOPE_TEXT = "Leo, today brings clarity and bold energy."


# ── GET /api/horoscope/daily ──────────────────────────────────────────────────

class TestDailyHoroscope:
    def test_daily_horoscope_returns_200(self, free_client):
        """
        WHAT: /horoscope/daily returns 200 with zodiac_sign, date, and horoscope text.
        WHY: Horoscope is the first card on the home screen — must always work.
        """
        with patch("app.api.horoscope.generate_daily_horoscope", return_value=_HOROSCOPE_TEXT):
            resp = free_client.get("/api/horoscope/daily")
        assert resp.status_code == 200
        body = resp.json()
        assert body["zodiac_sign"] == "Leo"
        assert body["horoscope"] == _HOROSCOPE_TEXT
        assert "date" in body
        assert body["language"] == "en"

    def test_daily_horoscope_requires_auth(self):
        """WHAT: /horoscope/daily without a token returns 401/403."""
        with TestClient(app, raise_server_exceptions=False) as raw:
            resp = raw.get("/api/horoscope/daily")
        assert resp.status_code in (401, 403)


# ── GET /api/horoscope/weekly ─────────────────────────────────────────────────

class TestWeeklyHoroscope:
    def test_weekly_horoscope_premium_returns_200(self, premium_client):
        """
        WHAT: A premium user can access /horoscope/weekly and receives a weekly overview.
        WHY: Weekly horoscope is a premium differentiator — must work for paying users.
        """
        with patch("app.api.horoscope.generate_daily_horoscope", return_value="A week of growth."):
            resp = premium_client.get("/api/horoscope/weekly")
        assert resp.status_code == 200
        body = resp.json()
        assert body["zodiac_sign"] == "Leo"
        assert "week_start" in body
        assert "week_end" in body
        assert body["horoscope"] == "A week of growth."

    def test_weekly_horoscope_free_user_403(self, free_client):
        """
        WHAT: A free user gets 403 on /horoscope/weekly.
        WHY: Premium gate must be enforced server-side — can't just hide it in UI.
        """
        resp = free_client.get("/api/horoscope/weekly")
        assert resp.status_code == 403


# ── GET /api/numerology/profile ──────────────────────────────────────────────

class TestNumerologyProfile:
    def test_numerology_profile_returns_correct_fields(self, free_client):
        """
        WHAT: /numerology/profile returns life_number, personal_year, personal_month,
        and the full meaning dict for the life number.
        WHY: These numbers are shown prominently on the user profile screen.
        """
        resp = free_client.get("/api/numerology/profile")
        assert resp.status_code == 200
        body = resp.json()
        assert "life_number" in body
        assert "personal_year" in body
        assert "personal_month" in body
        assert "life_number_info" in body
        assert "birth_date" in body

    def test_numerology_life_number_is_valid(self, free_client):
        """
        WHAT: The returned life_number is a valid value (1–9 or master number).
        WHY: An out-of-range number would confuse users and break frontend display.
        """
        resp = free_client.get("/api/numerology/profile")
        assert resp.status_code == 200
        life_number = resp.json()["life_number"]
        valid = set(range(1, 10)) | {11, 22, 33}
        assert life_number in valid

    def test_numerology_profile_requires_auth(self):
        """WHAT: /numerology/profile without token returns 401/403."""
        with TestClient(app, raise_server_exceptions=False) as raw:
            resp = raw.get("/api/numerology/profile")
        assert resp.status_code in (401, 403)

    def test_numerology_life_number_info_has_descriptions(self, free_client):
        """
        WHAT: The life_number_info object contains both English and Spanish descriptions.
        WHY: The app is bilingual from day one — both languages must be present.
        """
        resp = free_client.get("/api/numerology/profile")
        info = resp.json()["life_number_info"]
        assert info is not None
        assert len(info["description_en"]) > 10
        assert len(info["description_es"]) > 10
