from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "apply-reviewed-terraform-plan.sh").read_text(encoding="utf-8")


def test_apply_wrapper_requires_explicit_spend_authorization():
    assert "RIPPLE_AWS_SPEND_AUTHORIZED" in SCRIPT
    assert '!= "true"' in SCRIPT
    assert "explicit AWS spend authorization is required" in SCRIPT


def test_apply_wrapper_requires_exact_reviewed_plan_checksum():
    assert "RIPPLE_REVIEWED_PLAN" in SCRIPT
    assert "RIPPLE_REVIEWED_PLAN_SHA256" in SCRIPT
    assert 'sha256sum "${RIPPLE_REVIEWED_PLAN}"' in SCRIPT
    assert "checksum does not match" in SCRIPT


def test_apply_wrapper_applies_only_reviewed_binary_plan():
    assert 'terraform apply "${RIPPLE_REVIEWED_PLAN}"' in SCRIPT
    assert "terraform apply -auto-approve" not in SCRIPT
    assert "terraform apply ." not in SCRIPT


def test_apply_wrapper_verifies_idempotence_after_apply():
    assert "terraform plan -detailed-exitcode" in SCRIPT
    assert "re-plan returned no changes" in SCRIPT
    assert "re-plan contains changes after apply" in SCRIPT


def test_apply_wrapper_does_not_claim_to_authorize_spend():
    assert "does not grant authorization itself" in SCRIPT
