from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "check-stripe-webhook-reachability.sh").read_text(encoding="utf-8")


def test_stripe_webhook_reachability_targets_public_webhook_route():
    assert "/billing/webhook" in SCRIPT
    assert "curl" in SCRIPT
    assert "Stripe-Signature" in SCRIPT
    assert "--request POST" in SCRIPT


def test_configured_webhook_requires_invalid_signature_response():
    assert '[[ "${status}" != "400" ]]' in SCRIPT
    assert "reachable and rejects the invalid signature" in SCRIPT


def test_unconfigured_route_can_prove_reachability_without_claiming_configuration():
    assert '[[ "${status}" != "400" && "${status}" != "503" ]]' in SCRIPT
    assert "configured processing was not required" in SCRIPT


def test_reachability_probe_never_contains_real_stripe_credentials():
    assert "sk_live_" not in SCRIPT
    assert "whsec_" not in SCRIPT
