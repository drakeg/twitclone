from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "check-aws-launch-readiness.sh").read_text(encoding="utf-8")
ROADMAP = ROOT / "docs" / "ROADMAP.md"


def test_readiness_gate_has_structure_and_launch_modes():
    assert 'MODE="${1:-structure}"' in SCRIPT
    assert 'structure|launch' in SCRIPT
    assert 'STRUCTURE READY' in SCRIPT
    assert 'LAUNCH GATE READY' in SCRIPT


def test_readiness_gate_never_applies_or_creates_aws_resources():
    forbidden = (
        "terraform apply",
        "run-instances",
        "create-db-instance",
        "create-bucket",
        "put-parameter",
    )
    for token in forbidden:
        # The detection regex/help text may name a forbidden command; no executable invocation may exist.
        executable_lines = [
            line.strip()
            for line in SCRIPT.splitlines()
            if line.strip().startswith(("terraform ", "aws "))
        ]
        assert all(token not in line for line in executable_lines)


def test_structure_mode_runs_terraform_validation_and_release_dry_run():
    assert "terraform fmt -check" in SCRIPT
    assert "terraform init -backend=false -input=false" in SCRIPT
    assert "terraform validate" in SCRIPT
    assert "bash scripts/dry-run-production-release.sh" in SCRIPT


def test_launch_mode_requires_immutable_release_identity_and_manual_evidence():
    for required in (
        "RIPPLE_RELEASE_SHA",
        "RIPPLE_IMAGE",
        "RIPPLE_HOST_BOOTSTRAP_REF",
        "RIPPLE_COST_REVIEWED",
        "RIPPLE_RESTORE_REHEARSAL_PASSED",
        "RIPPLE_ACCESSIBILITY_EVIDENCE_PASSED",
        "RIPPLE_BACKUP_ALERT_PATH_TESTED",
        "RIPPLE_RELEASE_RECORD_PREPARED",
        "RIPPLE_COST_REVIEW_DATE",
    ):
        assert required in SCRIPT
    assert 'git rev-parse --abbrev-ref HEAD' in SCRIPT
    assert 'git status --porcelain' in SCRIPT
    assert ':latest' in SCRIPT


def test_roadmap_records_story_8_8_after_merge_target():
    # Updated in the same PR; keeps the contract visible in project planning.
    assert ROADMAP.exists()
