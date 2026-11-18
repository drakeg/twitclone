from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "aws-activation-handoff.md").read_text(encoding="utf-8")


def test_activation_handoff_preserves_spend_boundary():
    assert "Nothing in this document authorizes AWS spend" in DOC
    assert "RIPPLE_AWS_SPEND_AUTHORIZED=true" in DOC


def test_activation_handoff_uses_existing_guarded_workflows():
    for required in (
        "validate-terraform-plan.py",
        "apply-reviewed-terraform-plan.sh",
        "check-aws-launch-readiness.sh launch",
        "RIPPLE_REVIEWED_PLAN_SHA256",
        "RIPPLE_COST_REVIEW_DATE",
    ):
        assert required in DOC


def test_activation_handoff_keeps_live_evidence_explicit():
    for required in (
        "RDS is private",
        "S3 media is private",
        "Stripe webhook public reachability",
        "isolated restore rehearsal",
        "NVDA/VoiceOver",
        "real monthly bill",
    ):
        assert required in DOC
