"""
RevenueCat webhook endpoint.

Security model:
- RevenueCat signs every payload with HMAC-SHA256 using the shared secret.
- We verify the signature before processing anything.
- Invalid signatures → 401 (not 400, to avoid leaking info about our format).
- We respond 200 immediately and process synchronously (webhook payloads are small).
- All events are idempotent — re-processing the same event ID is safe.

Docs: https://www.revenuecat.com/docs/integrations/webhooks
"""
import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.config import settings
from app.db.database import get_session
from app.services.subscriptions import dispatch_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_revenuecat_signature(payload: bytes, signature_header: str | None) -> bool:
    """
    Verify RevenueCat webhook HMAC-SHA256 signature.

    RevenueCat sends: X-RevenueCat-Signature: <hex_digest>
    We compute:  hmac.new(secret, payload, sha256).hexdigest()
    and compare using a constant-time comparison to prevent timing attacks.

    Returns True if signature is valid or if REVENUECAT_WEBHOOK_SECRET is not
    configured (development mode — skip verification).
    """
    secret = settings.REVENUECAT_WEBHOOK_SECRET
    if not secret:
        logger.warning(
            "REVENUECAT_WEBHOOK_SECRET not set — skipping signature verification (dev mode)"
        )
        return True

    if not signature_header:
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header.lower())


@router.post(
    "/revenuecat",
    status_code=status.HTTP_200_OK,
    summary="RevenueCat subscription webhook",
)
async def revenuecat_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Receive and process RevenueCat subscription lifecycle events.

    Handles: INITIAL_PURCHASE, RENEWAL, CANCELLATION, EXPIRATION, BILLING_ISSUE.
    Rejects requests with invalid HMAC-SHA256 signatures.
    Returns 200 for all valid (including unhandled) event types.
    """
    # Read raw body BEFORE parsing JSON — we need bytes for HMAC
    body = await request.body()

    # Verify signature
    signature = request.headers.get("X-RevenueCat-Signature")
    if not _verify_revenuecat_signature(body, signature):
        logger.warning(
            "RevenueCat webhook rejected: invalid signature from %s",
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Parse event
    try:
        event = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = event.get("event", {}).get("type", "unknown")
    event_id = event.get("event", {}).get("id", "?")
    logger.info("RevenueCat webhook received: type=%s id=%s", event_type, event_id)

    # Dispatch to subscription service
    result = dispatch_event(session, event)
    return {"status": "ok", "result": result, "event_type": event_type}
