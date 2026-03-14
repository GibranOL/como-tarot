"""
Subscription service — handles RevenueCat webhook events.

Responsibilities:
- Activate premium on INITIAL_PURCHASE / RENEWAL
- Schedule expiration on CANCELLATION
- Deactivate on EXPIRATION / BILLING_ISSUE
- Keep is_premium on the users table in sync (avoids an extra JOIN on every request)

All methods are pure DB operations — no external API calls — making them
trivially testable and fast.
"""
import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.user import User
from app.models.subscription import Subscription

logger = logging.getLogger(__name__)

# RevenueCat event types we handle
_ACTIVATE_EVENTS = {"INITIAL_PURCHASE", "RENEWAL", "UNCANCELLATION"}
_CANCEL_EVENTS = {"CANCELLATION"}
_EXPIRE_EVENTS = {"EXPIRATION", "BILLING_ISSUE"}


def _sync_user_premium(session: Session, user_id: str, is_premium: bool) -> None:
    """Keep users.is_premium in sync after any subscription change."""
    import uuid
    user = session.get(User, uuid.UUID(user_id))
    if user:
        user.is_premium = is_premium
        session.add(user)


def handle_initial_purchase(
    session: Session,
    user_id: str,
    product_id: str,
    expires_at: datetime | None,
    revenue_cat_id: str,
) -> None:
    """
    Activate premium on first purchase.
    Creates the subscription row if it doesn't exist yet (edge case: user
    bought before our DB row was created).
    """
    import uuid

    sub = session.exec(
        select(Subscription).where(Subscription.user_id == uuid.UUID(user_id))
    ).first()

    plan = "premium_annual" if "annual" in product_id.lower() else "premium_monthly"

    if sub is None:
        sub = Subscription(
            user_id=uuid.UUID(user_id),
            plan=plan,
            revenue_cat_id=revenue_cat_id,
            started_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
        )
        session.add(sub)
    else:
        sub.plan = plan
        sub.revenue_cat_id = revenue_cat_id
        sub.expires_at = expires_at
        sub.is_active = True
        sub.updated_at = datetime.now(timezone.utc)
        session.add(sub)

    _sync_user_premium(session, user_id, True)
    session.commit()
    logger.info("Premium activated for user %s (plan=%s)", user_id, plan)


def handle_renewal(
    session: Session,
    user_id: str,
    expires_at: datetime | None,
) -> None:
    """Extend the subscription expiration date on renewal."""
    import uuid

    sub = session.exec(
        select(Subscription).where(Subscription.user_id == uuid.UUID(user_id))
    ).first()

    if sub is None:
        logger.warning("Renewal for unknown user %s — no subscription row found", user_id)
        return

    sub.expires_at = expires_at
    sub.is_active = True
    sub.updated_at = datetime.now(timezone.utc)
    session.add(sub)
    _sync_user_premium(session, user_id, True)
    session.commit()
    logger.info("Subscription renewed for user %s, expires=%s", user_id, expires_at)


def handle_cancellation(
    session: Session,
    user_id: str,
    expires_at: datetime | None,
) -> None:
    """
    Mark subscription as cancelled.
    User keeps premium access until expires_at — is_active stays True
    but we record the cancellation via plan staying unchanged.
    RevenueCat will fire EXPIRATION when access actually ends.
    """
    import uuid

    sub = session.exec(
        select(Subscription).where(Subscription.user_id == uuid.UUID(user_id))
    ).first()

    if sub is None:
        logger.warning("Cancellation for unknown user %s", user_id)
        return

    # Keep access until expiry — EXPIRATION event will deactivate
    sub.expires_at = expires_at
    sub.updated_at = datetime.now(timezone.utc)
    session.add(sub)
    session.commit()
    logger.info("Subscription cancelled for user %s, access until %s", user_id, expires_at)


def handle_expiration(session: Session, user_id: str) -> None:
    """
    Deactivate subscription on expiration or billing failure.
    User loses premium access immediately.
    """
    import uuid

    sub = session.exec(
        select(Subscription).where(Subscription.user_id == uuid.UUID(user_id))
    ).first()

    if sub is None:
        logger.warning("Expiration for unknown user %s", user_id)
        return

    sub.plan = "free"
    sub.is_active = False
    sub.updated_at = datetime.now(timezone.utc)
    session.add(sub)
    _sync_user_premium(session, user_id, False)
    session.commit()
    logger.info("Subscription expired/deactivated for user %s", user_id)


def dispatch_event(session: Session, event: dict) -> str:
    """
    Route a RevenueCat webhook event to the correct handler.
    Returns a short status string for logging.

    Expected event structure (RevenueCat V2 format):
    {
      "event": {
        "type": "INITIAL_PURCHASE" | "RENEWAL" | "CANCELLATION" | "EXPIRATION" | ...,
        "app_user_id": "<our user UUID>",
        "product_id": "cosmo_premium_monthly",
        "expiration_at_ms": 1234567890000,
        "id": "<revenuecat event id>",
        ...
      }
    }
    """
    evt = event.get("event", {})
    event_type = evt.get("type", "")
    user_id = evt.get("app_user_id", "")
    product_id = evt.get("product_id", "")
    revenue_cat_id = evt.get("id", "")

    if not user_id:
        logger.warning("RevenueCat event missing app_user_id: %s", event_type)
        return "missing_user_id"

    # Parse expiration timestamp (milliseconds → datetime)
    expires_at: datetime | None = None
    exp_ms = evt.get("expiration_at_ms")
    if exp_ms:
        try:
            expires_at = datetime.fromtimestamp(int(exp_ms) / 1000, tz=timezone.utc)
        except (ValueError, OSError):
            expires_at = None

    if event_type in _ACTIVATE_EVENTS:
        handle_initial_purchase(session, user_id, product_id, expires_at, revenue_cat_id)
        return "activated"

    if event_type == "RENEWAL":
        handle_renewal(session, user_id, expires_at)
        return "renewed"

    if event_type in _CANCEL_EVENTS:
        handle_cancellation(session, user_id, expires_at)
        return "cancelled"

    if event_type in _EXPIRE_EVENTS:
        handle_expiration(session, user_id)
        return "expired"

    logger.info("Unhandled RevenueCat event type: %s", event_type)
    return "ignored"
