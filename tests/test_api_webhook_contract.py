"""Sprint 16 Story 16.5 webhook contract regression coverage."""

from datetime import UTC, datetime

import pytest

from twitclone.api.webhooks import (
    DEFAULT_RETRY_DELAYS_SECONDS,
    build_webhook_event,
    canonical_webhook_payload,
    sign_webhook_payload,
    verify_webhook_signature,
)


def test_webhook_event_is_stable_and_versioned():
    event = build_webhook_event(
        "post.created",
        {"post": {"id": 42}},
        event_id="evt_test",
        occurred_at=datetime(2026, 9, 14, 3, 30, tzinfo=UTC),
    )
    assert event == {
        "id": "evt_test",
        "type": "post.created",
        "version": "v1",
        "occurred_at": "2026-09-14T03:30:00Z",
        "data": {"post": {"id": 42}},
    }


def test_webhook_rejects_unsupported_event_types():
    with pytest.raises(ValueError, match="unsupported webhook event type"):
        build_webhook_event("user.exported", {})


def test_canonical_payload_is_deterministic():
    first = canonical_webhook_payload({"b": 2, "a": 1})
    second = canonical_webhook_payload({"a": 1, "b": 2})
    assert first == second == b'{"a":1,"b":2}'


def test_signature_verification_accepts_valid_current_payload():
    payload = b'{"id":"evt_test"}'
    signature = sign_webhook_payload("secret", payload, timestamp=1000)
    assert verify_webhook_signature("secret", payload, signature, now=1000)


def test_signature_verification_rejects_tampering_wrong_secret_and_replay():
    payload = b'{"id":"evt_test"}'
    signature = sign_webhook_payload("secret", payload, timestamp=1000)
    assert not verify_webhook_signature("wrong", payload, signature, now=1000)
    assert not verify_webhook_signature("secret", b'{"id":"changed"}', signature, now=1000)
    assert not verify_webhook_signature("secret", payload, signature, now=1301, tolerance_seconds=300)


def test_signature_header_can_rotate_with_multiple_v1_values():
    payload = b'{"id":"evt_test"}'
    old_signature = sign_webhook_payload("old-secret", payload, timestamp=1000)
    new_signature = sign_webhook_payload("new-secret", payload, timestamp=1000)
    combined = old_signature + ",v1=" + new_signature.split("v1=", 1)[1]
    assert verify_webhook_signature("new-secret", payload, combined, now=1000)


def test_retry_contract_is_bounded_and_nonzero():
    assert DEFAULT_RETRY_DELAYS_SECONDS == (60, 300, 1800, 7200, 21600)
    assert all(delay > 0 for delay in DEFAULT_RETRY_DELAYS_SECONDS)
