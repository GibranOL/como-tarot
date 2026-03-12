"""
Integration tests for tarot endpoints.

WHY: These tests exercise the full HTTP stack (routing, validation, business
logic, DB persistence) without hitting real Supabase or Gemini. We mock only
the external boundaries: JWT validation and the AI service.
"""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_session
from app.main import app
from app.models.user import User
from app.security.dependencies import get_current_user

# ── Fixtures ─────────────────────────────────────────────────────────────────
# test_engine and db_session come from tests/integration/conftest.py


def _make_user(is_premium: bool = False) -> User:
    uid = uuid.uuid4()
    return User(
        id=uid,
        email=f"tarot-{uid.hex[:8]}@cosmo.mx",
        full_name="Test User",
        auth_provider="email",
        birth_date=date(1990, 7, 25),
        zodiac_sign="Leo",
        life_number=6,
        preferred_language="en",
        timezone="America/Mexico_City",
        is_premium=is_premium,
        onboarding_answers={"reading_style": "reflective"},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture(name="free_user")
def free_user_fixture():
    return _make_user(is_premium=False)


@pytest.fixture(name="premium_user")
def premium_user_fixture():
    return _make_user(is_premium=True)


@pytest.fixture(name="client")
def client_fixture(db_session, free_user):
    """Test client: PostgreSQL DB + free user persisted and injected as current_user.
    User is inserted so FK constraints on daily_readings/tarotist_questions are satisfied."""
    db_session.add(free_user)
    db_session.commit()
    db_session.refresh(free_user)

    def get_session_override():
        yield db_session

    def get_user_override():
        return free_user

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_user_override
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="premium_client")
def premium_client_fixture(db_session, premium_user):
    """Test client: PostgreSQL DB + premium user persisted and injected."""
    db_session.add(premium_user)
    db_session.commit()
    db_session.refresh(premium_user)

    def get_session_override():
        yield db_session

    def get_user_override():
        return premium_user

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_user_override
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


_AI_RESPONSE = "The stars reveal a path of transformation and growth."


# ── GET /api/tarot/daily ──────────────────────────────────────────────────────

class TestDailyReading:
    def test_daily_reading_creates_new(self, client):
        """
        WHAT: First call to /daily for a user creates a new reading and returns 200.
        WHY: Core feature — must work end-to-end (draw + AI + persist).
        """
        with patch("app.api.tarot.generate_tarot_interpretation", return_value=_AI_RESPONSE):
            resp = client.get("/api/tarot/daily")
        assert resp.status_code == 200
        body = resp.json()
        assert "cards_drawn" in body
        assert len(body["cards_drawn"]) == 3
        assert body["ai_interpretation"] == _AI_RESPONSE
        assert body["language"] == "en"

    def test_daily_reading_returns_cached(self, client):
        """
        WHAT: Second call on the same day returns the cached reading (no new AI call).
        WHY: We must not bill Gemini twice for the same user's daily reading.
        """
        with patch("app.api.tarot.generate_tarot_interpretation", return_value=_AI_RESPONSE) as mock_ai:
            resp1 = client.get("/api/tarot/daily")
            resp2 = client.get("/api/tarot/daily")

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        # Both responses should have the same reading id
        assert resp1.json()["id"] == resp2.json()["id"]
        # AI was called at most once (cache hit on second call)
        assert mock_ai.call_count <= 1

    def test_daily_reading_invalid_spread_type_422(self, client):
        """
        WHAT: Passing an invalid spread_type query parameter returns 422.
        WHY: Input validation must prevent garbage from reaching the service layer.
        """
        resp = client.get("/api/tarot/daily?spread_type=invalid_spread")
        assert resp.status_code == 422

    def test_daily_reading_requires_auth(self):
        """
        WHAT: Calling /daily without a token returns 403 (no credentials).
        WHY: Reading history is private — unauthenticated access must be blocked.
        """
        with TestClient(app, raise_server_exceptions=False) as raw_client:
            resp = raw_client.get("/api/tarot/daily")
        assert resp.status_code in (401, 403)


# ── POST /api/tarot/ask ───────────────────────────────────────────────────────

class TestAskTarotist:
    def test_ask_tarotist_free_user(self, client):
        """
        WHAT: A free user can ask one question and receives an AI answer.
        WHY: Free tier includes 1 question/day — must work correctly.
        """
        with patch("app.api.tarot.answer_tarotist_question", return_value="The cards say: trust yourself."):
            resp = client.post("/api/tarot/ask", json={"question": "Will I find my purpose?"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["answer"] == "The cards say: trust yourself."
        assert body["question"] == "Will I find my purpose?"

    def test_ask_tarotist_empty_question_422(self, client):
        """
        WHAT: An empty question returns 422 validation error.
        WHY: We must never send a blank prompt to Gemini.
        """
        resp = client.post("/api/tarot/ask", json={"question": "   "})
        assert resp.status_code == 422

    def test_ask_tarotist_question_too_long_422(self, client):
        """
        WHAT: A question exceeding 500 characters returns 422.
        WHY: Max length validation must be enforced at the schema level.
        """
        resp = client.post("/api/tarot/ask", json={"question": "x" * 501})
        assert resp.status_code == 422

    def test_ask_tarotist_requires_auth(self):
        """WHAT: /ask without a token returns 401/403."""
        with TestClient(app, raise_server_exceptions=False) as raw_client:
            resp = raw_client.post("/api/tarot/ask", json={"question": "test"})
        assert resp.status_code in (401, 403)


# ── GET /api/tarot/history ────────────────────────────────────────────────────

class TestReadingHistory:
    def test_history_returns_list(self, client):
        """
        WHAT: /history returns a paginated list of readings.
        WHY: Users must be able to review past readings — core feature.
        """
        with patch("app.api.tarot.generate_tarot_interpretation", return_value=_AI_RESPONSE):
            client.get("/api/tarot/daily")  # ensure at least one reading exists

        resp = client.get("/api/tarot/history")
        assert resp.status_code == 200
        body = resp.json()
        assert "readings" in body
        assert "total" in body
        assert isinstance(body["readings"], list)

    def test_history_pagination(self, client):
        """
        WHAT: page and page_size query params are respected.
        WHY: Unbounded queries would blow up the DB for users with long histories.
        """
        resp = client.get("/api/tarot/history?page=1&page_size=5")
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 5
        assert len(body["readings"]) <= 5

    def test_history_invalid_page_size_422(self, client):
        """WHAT: page_size=0 returns 422 (must be ≥ 1)."""
        resp = client.get("/api/tarot/history?page_size=0")
        assert resp.status_code == 422
