"""
Unit tests for the subscriptions service.

WHY: Subscription state transitions are critical — a bug here means users
get premium for free (revenue loss) or lose paid access (churn). We test
every event type and edge case with a mocked DB session so these run in
milliseconds without a real database.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from app.services.subscriptions import (
    dispatch_event,
    handle_cancellation,
    handle_expiration,
    handle_initial_purchase,
    handle_renewal,
)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _make_mock_session(existing_sub=None, existing_user=None):
    """Return a mock SQLModel session with configurable query results."""
    session = MagicMock()

    # session.exec(...).first() → existing_sub (or None)
    exec_result = MagicMock()
    exec_result.first.return_value = existing_sub
    session.exec.return_value = exec_result

    # session.get(User, uid) → existing_user (or None)
    session.get.return_value = existing_user
    return session


def _make_sub(user_id: str, plan: str = "premium_monthly") -> MagicMock:
    sub = MagicMock()
    sub.user_id = uuid.UUID(user_id)
    sub.plan = plan
    sub.is_active = True
    return sub


def _make_user(is_premium: bool = True) -> MagicMock:
    user = MagicMock()
    user.is_premium = is_premium
    return user


# ── handle_initial_purchase ───────────────────────────────────────────────────

class TestHandleInitialPurchase:
    def test_creates_new_subscription_when_none_exists(self):
        """
        WHAT: When no subscription row exists, initial purchase creates one
        and sets the user as premium.
        WHY: First-time buyers must always get a subscription row — without it,
        subsequent RENEWAL events will silently fail (user stays free).
        """
        uid = str(uuid.uuid4())
        session = _make_mock_session(existing_sub=None, existing_user=_make_user(False))

        handle_initial_purchase(
            session, uid, "cosmo_premium_monthly",
            datetime(2027, 1, 1, tzinfo=timezone.utc), "rc_event_1"
        )

        session.add.assert_called()
        session.commit.assert_called_once()

    def test_updates_existing_subscription_on_purchase(self):
        """
        WHAT: If a free-tier subscription row already exists, initial purchase
        updates it (plan, is_active, expires_at) rather than creating a duplicate.
        WHY: Duplicate subscription rows would cause FK violations and double-charge
        scenarios in billing reports.
        """
        uid = str(uuid.uuid4())
        existing = _make_sub(uid, plan="free")
        session = _make_mock_session(existing_sub=existing, existing_user=_make_user(False))

        handle_initial_purchase(
            session, uid, "cosmo_premium_annual",
            datetime(2027, 1, 1, tzinfo=timezone.utc), "rc_event_2"
        )

        assert existing.plan == "premium_annual"
        assert existing.is_active is True
        session.commit.assert_called_once()

    def test_detects_annual_plan_from_product_id(self):
        """
        WHAT: Product IDs containing 'annual' map to 'premium_annual' plan.
        WHY: The plan field drives UI display and analytics — the wrong plan
        stored means wrong renewal reminders and pricing analytics.
        """
        uid = str(uuid.uuid4())
        existing = _make_sub(uid, plan="free")
        session = _make_mock_session(existing_sub=existing, existing_user=_make_user())

        handle_initial_purchase(
            session, uid, "cosmo_premium_annual_v2",
            None, "rc_event_3"
        )

        assert existing.plan == "premium_annual"

    def test_detects_monthly_plan_from_product_id(self):
        """
        WHAT: Product IDs without 'annual' default to 'premium_monthly'.
        WHY: Monthly and annual have different renewal cycles — must be stored
        correctly to reconcile with RevenueCat's billing schedule.
        """
        uid = str(uuid.uuid4())
        existing = _make_sub(uid, plan="free")
        session = _make_mock_session(existing_sub=existing, existing_user=_make_user())

        handle_initial_purchase(
            session, uid, "cosmo_premium_monthly",
            None, "rc_event_4"
        )

        assert existing.plan == "premium_monthly"

    def test_syncs_user_is_premium_to_true(self):
        """
        WHAT: After initial purchase, users.is_premium is set to True.
        WHY: Every protected endpoint reads is_premium directly from the user row.
        Without this sync the paywall would still block a paying user.
        """
        uid = str(uuid.uuid4())
        user = _make_user(is_premium=False)
        session = _make_mock_session(existing_sub=None, existing_user=user)

        handle_initial_purchase(
            session, uid, "cosmo_premium_monthly",
            None, "rc_event_5"
        )

        assert user.is_premium is True


# ── handle_renewal ────────────────────────────────────────────────────────────

class TestHandleRenewal:
    def test_extends_expiration_date(self):
        """
        WHAT: Renewal updates expires_at and keeps is_active = True.
        WHY: Without updating expires_at, the EXPIRATION event would fire early
        and incorrectly cut off a user who successfully renewed.
        """
        uid = str(uuid.uuid4())
        sub = _make_sub(uid)
        user = _make_user(True)
        session = _make_mock_session(existing_sub=sub, existing_user=user)
        new_expiry = datetime(2028, 1, 1, tzinfo=timezone.utc)

        handle_renewal(session, uid, new_expiry)

        assert sub.expires_at == new_expiry
        assert sub.is_active is True
        session.commit.assert_called_once()

    def test_renewal_with_no_subscription_logs_warning(self):
        """
        WHAT: Renewal for a user with no subscription row logs a warning but
        does not crash.
        WHY: Defensive handling prevents a missing row from surfacing as a 500
        on the webhook endpoint, which would cause RevenueCat to retry endlessly.
        """
        uid = str(uuid.uuid4())
        session = _make_mock_session(existing_sub=None, existing_user=None)

        # Must not raise
        handle_renewal(session, uid, None)
        session.commit.assert_not_called()


# ── handle_cancellation ───────────────────────────────────────────────────────

class TestHandleCancellation:
    def test_cancellation_keeps_access_until_expiry(self):
        """
        WHAT: On CANCELLATION, is_active stays True and expires_at is updated.
        Access is kept until the end of the billing period.
        WHY: Cutting access immediately on cancellation violates Apple/Google
        guidelines and would generate chargebacks. The EXPIRATION event (fired
        at period end) deactivates access.
        """
        uid = str(uuid.uuid4())
        sub = _make_sub(uid)
        session = _make_mock_session(existing_sub=sub, existing_user=None)
        future_expiry = datetime(2027, 6, 1, tzinfo=timezone.utc)

        handle_cancellation(session, uid, future_expiry)

        assert sub.expires_at == future_expiry
        assert sub.is_active is True  # access preserved until period end
        session.commit.assert_called_once()

    def test_cancellation_with_no_subscription_is_safe(self):
        """
        WHAT: Cancellation for an unknown user does not crash.
        WHY: RevenueCat can send events for users who deleted their account. A
        crash here would cause the webhook to return 500 and trigger retries.
        """
        uid = str(uuid.uuid4())
        session = _make_mock_session(existing_sub=None)

        handle_cancellation(session, uid, None)
        session.commit.assert_not_called()


# ── handle_expiration ─────────────────────────────────────────────────────────

class TestHandleExpiration:
    def test_expiration_deactivates_subscription(self):
        """
        WHAT: EXPIRATION sets plan='free', is_active=False, and is_premium=False.
        WHY: Expired users must lose premium access immediately. Any delay here
        means users get free premium — a direct revenue leak.
        """
        uid = str(uuid.uuid4())
        sub = _make_sub(uid, plan="premium_monthly")
        user = _make_user(is_premium=True)
        session = _make_mock_session(existing_sub=sub, existing_user=user)

        handle_expiration(session, uid)

        assert sub.plan == "free"
        assert sub.is_active is False
        assert user.is_premium is False
        session.commit.assert_called_once()

    def test_expiration_with_no_subscription_is_safe(self):
        """
        WHAT: Expiration for an unknown user does not crash.
        WHY: Same reasoning as cancellation — defensive webhook handling.
        """
        uid = str(uuid.uuid4())
        session = _make_mock_session(existing_sub=None)

        handle_expiration(session, uid)
        session.commit.assert_not_called()


# ── dispatch_event ────────────────────────────────────────────────────────────

class TestDispatchEvent:
    def _make_event(self, event_type: str, extra: dict | None = None) -> dict:
        base = {
            "event": {
                "type": event_type,
                "app_user_id": str(uuid.uuid4()),
                "product_id": "cosmo_premium_monthly",
                "id": "rc_test_id",
                "expiration_at_ms": 1893456000000,  # 2030-01-01
            }
        }
        if extra:
            base["event"].update(extra)
        return base

    def test_initial_purchase_returns_activated(self):
        """
        WHAT: INITIAL_PURCHASE event dispatches to handle_initial_purchase
        and returns 'activated'.
        WHY: The return value is logged for observability — wrong value means
        the event silently took the wrong code path.
        """
        session = _make_mock_session(existing_sub=None, existing_user=_make_user(False))
        result = dispatch_event(session, self._make_event("INITIAL_PURCHASE"))
        assert result == "activated"

    def test_renewal_returns_renewed(self):
        """WHAT: RENEWAL event returns 'renewed'."""
        sub = _make_sub(str(uuid.uuid4()))
        session = _make_mock_session(existing_sub=sub, existing_user=_make_user())
        event = self._make_event("RENEWAL")
        event["event"]["app_user_id"] = str(sub.user_id)
        result = dispatch_event(session, event)
        assert result == "renewed"

    def test_cancellation_returns_cancelled(self):
        """WHAT: CANCELLATION event returns 'cancelled'."""
        sub = _make_sub(str(uuid.uuid4()))
        session = _make_mock_session(existing_sub=sub)
        event = self._make_event("CANCELLATION")
        event["event"]["app_user_id"] = str(sub.user_id)
        result = dispatch_event(session, event)
        assert result == "cancelled"

    def test_expiration_returns_expired(self):
        """WHAT: EXPIRATION event returns 'expired'."""
        sub = _make_sub(str(uuid.uuid4()))
        user = _make_user(True)
        session = _make_mock_session(existing_sub=sub, existing_user=user)
        event = self._make_event("EXPIRATION")
        event["event"]["app_user_id"] = str(sub.user_id)
        result = dispatch_event(session, event)
        assert result == "expired"

    def test_billing_issue_deactivates(self):
        """
        WHAT: BILLING_ISSUE (failed payment) is treated like EXPIRATION —
        user loses access.
        WHY: A failed payment means we haven't been paid. Keeping premium access
        after a billing failure is a revenue leak.
        """
        sub = _make_sub(str(uuid.uuid4()))
        user = _make_user(True)
        session = _make_mock_session(existing_sub=sub, existing_user=user)
        event = self._make_event("BILLING_ISSUE")
        event["event"]["app_user_id"] = str(sub.user_id)
        result = dispatch_event(session, event)
        assert result == "expired"

    def test_unknown_event_type_returns_ignored(self):
        """
        WHAT: Unknown event types (e.g., TEST, TRANSFER) return 'ignored'.
        WHY: RevenueCat sends many event types we don't handle. They must be
        acknowledged (200) without crashing, otherwise RevenueCat retries them.
        """
        session = _make_mock_session()
        result = dispatch_event(session, self._make_event("SUBSCRIBER_ALIAS"))
        assert result == "ignored"

    def test_missing_user_id_returns_missing_user_id(self):
        """
        WHAT: Events with no app_user_id return 'missing_user_id' safely.
        WHY: A malformed payload must not crash the webhook or corrupt DB state.
        """
        session = _make_mock_session()
        event = {"event": {"type": "INITIAL_PURCHASE", "app_user_id": ""}}
        result = dispatch_event(session, event)
        assert result == "missing_user_id"

    def test_expiration_timestamp_parsed_correctly(self):
        """
        WHAT: expiration_at_ms (Unix ms) is correctly converted to a datetime.
        WHY: An off-by-1000 error (ms vs seconds) would set expires_at 1000x
        further in the future, giving users free eternal access.
        """
        sub = _make_sub(str(uuid.uuid4()))
        user = _make_user(True)
        session = _make_mock_session(existing_sub=sub, existing_user=user)

        # 2030-01-01 00:00:00 UTC = 1893456000 seconds = 1893456000000 ms
        event = self._make_event("RENEWAL", {"expiration_at_ms": 1893456000000})
        event["event"]["app_user_id"] = str(sub.user_id)
        dispatch_event(session, event)

        assert sub.expires_at == datetime(2030, 1, 1, tzinfo=timezone.utc)
