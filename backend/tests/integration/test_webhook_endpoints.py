"""
Integration tests for the RevenueCat webhook endpoint.

WHY: The webhook is the only external entry point that modifies subscription state.
A broken signature check means anyone on the internet can fake a purchase or
cancellation. These tests verify the full HTTP stack — routing, signature
verification, event parsing, and DB update — without hitting real RevenueCat.
"""
import hashlib
import hmac
import json
import uuid
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_session
from app.main import app
from app.models.user import User
from app.models.subscription import Subscription


# ── Helpers ───────────────────────────────────────────────────────────────────

_TEST_SECRET = "test_webhook_secret_32chars_long!"


def _sign(payload: bytes, secret: str = _TEST_SECRET) -> str:
    """Compute the expected HMAC-SHA256 signature for a payload."""
    return hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()


def _make_rc_event(
    event_type: str,
    user_id: str,
    product_id: str = "cosmo_premium_monthly",
    expiration_ms: int | None = 1893456000000,
) -> dict:
    """Build a minimal RevenueCat webhook payload."""
    evt: dict = {
        "type": event_type,
        "app_user_id": user_id,
        "product_id": product_id,
        "id": f"rc_test_{uuid.uuid4().hex[:8]}",
    }
    if expiration_ms is not None:
        evt["expiration_at_ms"] = expiration_ms
    return {"event": evt}


def _make_user(db_session, is_premium: bool = False) -> tuple[User, Subscription]:
    """Persist a user + free subscription row, return both."""
    uid = uuid.uuid4()
    user = User(
        id=uid,
        email=f"webhook-{uid.hex[:8]}@cosmo.mx",
        full_name="Webhook Test",
        auth_provider="email",
        birth_date=date(1990, 5, 20),
        zodiac_sign="Taurus",
        life_number=7,
        preferred_language="es",
        timezone="America/Mexico_City",
        is_premium=is_premium,
        onboarding_answers=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    sub = Subscription(
        user_id=uid,
        plan="premium_monthly" if is_premium else "free",
        is_active=True,
    )
    db_session.add(user)
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(sub)
    return user, sub


# ── Signature verification ────────────────────────────────────────────────────

class TestSignatureVerification:
    """
    Signature checks run before any DB access, so these tests need no DB.
    They use a raw TestClient without session override.
    """

    def test_invalid_signature_returns_401(self):
        """
        WHAT: A webhook with a wrong HMAC signature is rejected with 401.
        WHY: Without this, any attacker can forge a RENEWAL or EXPIRATION event
        and arbitrarily grant or revoke premium access for any user.
        """
        with patch("app.api.webhooks.settings") as mock_settings:
            mock_settings.REVENUECAT_WEBHOOK_SECRET = _TEST_SECRET
            payload = json.dumps({"event": {"type": "TEST"}}).encode()

            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post(
                    "/webhooks/revenuecat",
                    content=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-RevenueCat-Signature": "deadbeefdeadbeef",  # wrong
                    },
                )
        assert resp.status_code == 401

    def test_missing_signature_header_returns_401(self):
        """
        WHAT: A webhook with no signature header is rejected with 401.
        WHY: Requests with no signature are indistinguishable from forgeries —
        must be rejected even if the body looks valid.
        """
        with patch("app.api.webhooks.settings") as mock_settings:
            mock_settings.REVENUECAT_WEBHOOK_SECRET = _TEST_SECRET
            payload = json.dumps({"event": {"type": "TEST"}}).encode()

            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.post(
                    "/webhooks/revenuecat",
                    content=payload,
                    headers={"Content-Type": "application/json"},
                    # No X-RevenueCat-Signature
                )
        assert resp.status_code == 401

    def test_valid_signature_returns_200(self, db_session):
        """
        WHAT: A correctly signed webhook (valid HMAC) returns 200.
        WHY: The happy path must work — RevenueCat retries on non-200 responses,
        which would spam our webhook and potentially double-process events.
        """
        uid = str(uuid.uuid4())
        payload_dict = _make_rc_event("INITIAL_PURCHASE", uid)
        payload = json.dumps(payload_dict).encode()
        sig = _sign(payload)

        def get_session_override():
            yield db_session

        app.dependency_overrides[get_session] = get_session_override
        try:
            with patch("app.api.webhooks.settings") as mock_settings:
                mock_settings.REVENUECAT_WEBHOOK_SECRET = _TEST_SECRET
                with TestClient(app) as c:
                    resp = c.post(
                        "/webhooks/revenuecat",
                        content=payload,
                        headers={
                            "Content-Type": "application/json",
                            "X-RevenueCat-Signature": sig,
                        },
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_dev_mode_no_secret_skips_verification(self, db_session):
        """
        WHAT: When REVENUECAT_WEBHOOK_SECRET is empty (dev/test mode),
        signature verification is skipped and the request is processed.
        WHY: During local development we don't have a real RevenueCat webhook
        configured. Blocking all webhooks would make local testing impossible.
        """
        uid = str(uuid.uuid4())
        payload_dict = _make_rc_event("SUBSCRIBER_ALIAS", uid)
        payload = json.dumps(payload_dict).encode()

        def get_session_override():
            yield db_session

        app.dependency_overrides[get_session] = get_session_override
        try:
            with patch("app.api.webhooks.settings") as mock_settings:
                mock_settings.REVENUECAT_WEBHOOK_SECRET = ""  # dev mode
                with TestClient(app) as c:
                    resp = c.post(
                        "/webhooks/revenuecat",
                        content=payload,
                        headers={"Content-Type": "application/json"},
                        # No signature
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200


# ── Subscription lifecycle events ─────────────────────────────────────────────

class TestSubscriptionLifecycle:
    def _post_event(self, db_session, event_type: str, user_id: str) -> dict:
        """Helper: sign and post a webhook event, return response JSON."""
        payload_dict = _make_rc_event(event_type, user_id)
        payload = json.dumps(payload_dict).encode()
        sig = _sign(payload)

        def get_session_override():
            yield db_session

        app.dependency_overrides[get_session] = get_session_override
        try:
            with patch("app.api.webhooks.settings") as mock_settings:
                mock_settings.REVENUECAT_WEBHOOK_SECRET = _TEST_SECRET
                with TestClient(app) as c:
                    resp = c.post(
                        "/webhooks/revenuecat",
                        content=payload,
                        headers={
                            "Content-Type": "application/json",
                            "X-RevenueCat-Signature": sig,
                        },
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        return resp.json()

    def test_initial_purchase_activates_premium(self, db_session):
        """
        WHAT: INITIAL_PURCHASE webhook sets user.is_premium = True and
        subscription.plan = 'premium_monthly'.
        WHY: This is the money path — a paying user must get premium access
        the moment RevenueCat confirms the purchase.
        """
        user, sub = _make_user(db_session, is_premium=False)

        body = self._post_event(db_session, "INITIAL_PURCHASE", str(user.id))
        assert body["result"] == "activated"

        db_session.refresh(user)
        db_session.refresh(sub)
        assert user.is_premium is True
        assert sub.plan == "premium_monthly"
        assert sub.is_active is True

    def test_expiration_revokes_premium(self, db_session):
        """
        WHAT: EXPIRATION webhook sets user.is_premium = False and
        subscription.is_active = False.
        WHY: Expired users must lose access immediately. Keeping premium after
        expiration is a revenue leak that compounds daily.
        """
        user, sub = _make_user(db_session, is_premium=True)

        body = self._post_event(db_session, "EXPIRATION", str(user.id))
        assert body["result"] == "expired"

        db_session.refresh(user)
        db_session.refresh(sub)
        assert user.is_premium is False
        assert sub.is_active is False
        assert sub.plan == "free"

    def test_cancellation_keeps_access(self, db_session):
        """
        WHAT: CANCELLATION webhook keeps is_active = True (access until period end).
        WHY: Cancellation ≠ expiration. The user paid for the current period —
        they must keep access until it ends, or we violate store guidelines.
        """
        user, sub = _make_user(db_session, is_premium=True)

        body = self._post_event(db_session, "CANCELLATION", str(user.id))
        assert body["result"] == "cancelled"

        db_session.refresh(sub)
        assert sub.is_active is True  # still active until EXPIRATION fires

    def test_unknown_event_returns_ignored(self, db_session):
        """
        WHAT: Unknown event types (e.g., TRANSFER, TEST) are acknowledged with
        200 and result='ignored' without modifying the DB.
        WHY: RevenueCat sends many events we don't need to handle. Returning
        non-200 would cause retries that flood our webhook endpoint.
        """
        user, _ = _make_user(db_session)

        body = self._post_event(db_session, "TRANSFER", str(user.id))
        assert body["result"] == "ignored"


# ── Malformed payloads ────────────────────────────────────────────────────────

class TestMalformedPayloads:
    def test_invalid_json_returns_400(self, db_session):
        """
        WHAT: A request with non-JSON body returns 400.
        WHY: Prevents the endpoint from crashing on garbage payloads, which
        would cause RevenueCat to retry indefinitely.
        """
        payload = b"this is not json"
        sig = _sign(payload)

        def get_session_override():
            yield db_session

        app.dependency_overrides[get_session] = get_session_override
        try:
            with patch("app.api.webhooks.settings") as mock_settings:
                mock_settings.REVENUECAT_WEBHOOK_SECRET = _TEST_SECRET
                with TestClient(app, raise_server_exceptions=False) as c:
                    resp = c.post(
                        "/webhooks/revenuecat",
                        content=payload,
                        headers={
                            "Content-Type": "application/json",
                            "X-RevenueCat-Signature": sig,
                        },
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 400
