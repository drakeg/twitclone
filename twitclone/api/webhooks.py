"""Provider-neutral webhook contract primitives for Ripple integrations."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import hmac
import json
import time
import uuid

SUPPORTED_WEBHOOK_EVENTS = {"post.created"}
WEBHOOK_VERSION = "v1"
DEFAULT_REPLAY_TOLERANCE_SECONDS = 300
DEFAULT_RETRY_DELAYS_SECONDS = (60, 300, 1800, 7200, 21600)


def _utcnow():
    return datetime.now(UTC)


def build_webhook_event(event_type, data, *, event_id=None, occurred_at=None):
    """Build a stable webhook envelope for an explicitly supported event type."""
    if event_type not in SUPPORTED_WEBHOOK_EVENTS:
        raise ValueError("unsupported webhook event type")
    if not isinstance(data, dict):
        raise ValueError("webhook data must be an object")
    event_id = event_id or str(uuid.uuid4())
    occurred_at = occurred_at or _utcnow()
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)
    return {
        "id": event_id,
        "type": event_type,
        "version": WEBHOOK_VERSION,
        "occurred_at": occurred_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "data": data,
    }


def canonical_webhook_payload(event):
    """Return deterministic UTF-8 bytes for signing and delivery."""
    return json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign_webhook_payload(secret, payload, *, timestamp=None):
    """Return Stripe-style timestamped HMAC-SHA256 signature metadata."""
    if not secret:
        raise ValueError("webhook secret is required")
    timestamp = int(time.time() if timestamp is None else timestamp)
    body = payload if isinstance(payload, bytes) else bytes(payload)
    signed = str(timestamp).encode("ascii") + b"." + body
    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def verify_webhook_signature(secret, payload, signature_header, *, now=None, tolerance_seconds=DEFAULT_REPLAY_TOLERANCE_SECONDS):
    """Verify signature and reject stale/replayed delivery attempts outside the window."""
    if not secret or not signature_header:
        return False
    parts = {}
    for item in signature_header.split(","):
        key, separator, value = item.partition("=")
        if separator:
            parts.setdefault(key.strip(), []).append(value.strip())
    try:
        timestamp = int(parts.get("t", [""])[0])
    except ValueError:
        return False
    current = int(time.time() if now is None else now)
    if abs(current - timestamp) > tolerance_seconds:
        return False
    expected = sign_webhook_payload(secret, payload, timestamp=timestamp).split("v1=", 1)[1]
    return any(hmac.compare_digest(expected, candidate) for candidate in parts.get("v1", []))


__all__ = [
    "DEFAULT_REPLAY_TOLERANCE_SECONDS",
    "DEFAULT_RETRY_DELAYS_SECONDS",
    "SUPPORTED_WEBHOOK_EVENTS",
    "WEBHOOK_VERSION",
    "build_webhook_event",
    "canonical_webhook_payload",
    "sign_webhook_payload",
    "verify_webhook_signature",
]
