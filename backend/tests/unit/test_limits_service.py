"""
Unit tests for the usage limits service.
WHY: Free-tier limits protect revenue and AI costs. If limits don't work,
free users get unlimited access and premium loses its value proposition.
"""
import uuid
from datetime import date
from unittest.mock import MagicMock, patch

from app.services.limits import (
    check_user_limits,
    FREE_DAILY_READINGS,
)


def _mock_user(is_premium: bool = False) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_premium = is_premium
    return user


class TestFreeUserLimits:
    @patch("app.services.limits.get_questions_today", return_value=0)
    @patch("app.services.limits.get_readings_today", return_value=0)
    def test_free_user_can_read_once(self, mock_readings, mock_questions):
        """WHAT: A free user with 0 readings today can still read.
        WHY: Free tier allows 1 daily reading — must not block before the limit."""
        session = MagicMock()
        user = _mock_user(is_premium=False)
        result = check_user_limits(session, user)
        assert result["can_read"] is True
        assert result["can_ask"] is True
        assert result["is_premium"] is False

    @patch("app.services.limits.get_questions_today", return_value=1)
    @patch("app.services.limits.get_readings_today", return_value=1)
    def test_free_user_blocked_after_limit(self, mock_readings, mock_questions):
        """WHAT: A free user who has already used their daily quota is blocked.
        WHY: This is the core monetization gate — free users must be limited."""
        session = MagicMock()
        user = _mock_user(is_premium=False)
        result = check_user_limits(session, user)
        assert result["can_read"] is False
        assert result["can_ask"] is False
        assert result["daily_reading_limit"] == FREE_DAILY_READINGS


class TestPremiumUserLimits:
    @patch("app.services.limits.get_questions_today", return_value=50)
    @patch("app.services.limits.get_readings_today", return_value=50)
    def test_premium_user_unlimited(self, mock_readings, mock_questions):
        """WHAT: A premium user is never blocked, regardless of usage count.
        WHY: Premium users pay for unlimited access — limits must not apply."""
        session = MagicMock()
        user = _mock_user(is_premium=True)
        result = check_user_limits(session, user)
        assert result["can_read"] is True
        assert result["can_ask"] is True
        assert result["is_premium"] is True
        assert result["daily_reading_limit"] is None
        assert result["daily_question_limit"] is None


class TestLimitDateFiltering:
    @patch("app.services.limits.get_questions_today", return_value=0)
    @patch("app.services.limits.get_readings_today", return_value=0)
    @patch("app.services.limits._today_utc", return_value=date(2026, 3, 13))
    def test_limit_resets_at_midnight(self, mock_today, mock_readings, mock_questions):
        """WHAT: Mocking _today_utc to a new date resets the counters.
        WHY: Limits are per-day — a new UTC date must allow new reads/asks."""
        session = MagicMock()
        user = _mock_user(is_premium=False)
        result = check_user_limits(session, user)
        assert result["can_read"] is True
        assert result["readings_today"] == 0
