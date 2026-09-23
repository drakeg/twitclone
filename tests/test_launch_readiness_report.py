"""Sprint 19 launch-readiness reporting coverage."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "report-launch-readiness.py"


def _module():
    spec = importlib.util.spec_from_file_location("launch_readiness_report", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_report_is_blocked_without_manual_evidence():
    module = _module()
    report = module.build_report(ROOT, {})

    assert report["status"] == "blocked"
    assert report["spend_authorized"] is False
    assert report["provisioning_performed"] is False
    assert "cost_review" in report["incomplete_evidence"]
    assert "restore_rehearsal" in report["incomplete_evidence"]


def test_report_becomes_review_ready_when_evidence_is_complete():
    module = _module()
    env = {
        "RIPPLE_COST_REVIEWED": "true",
        "RIPPLE_COST_REVIEW_DATE": "2026-09-23",
        "RIPPLE_RESTORE_REHEARSAL_PASSED": "true",
        "RIPPLE_ACCESSIBILITY_EVIDENCE_PASSED": "true",
        "RIPPLE_BACKUP_ALERT_PATH_TESTED": "true",
        "RIPPLE_RELEASE_RECORD_PREPARED": "true",
    }

    report = module.build_report(ROOT, env)

    assert report["missing_artifacts"] == []
    assert report["incomplete_evidence"] == []
    assert report["status"] == "ready_for_launch_gate_review"


def test_invalid_cost_review_date_keeps_report_blocked():
    module = _module()
    env = {
        "RIPPLE_COST_REVIEWED": "true",
        "RIPPLE_COST_REVIEW_DATE": "09/23/2026",
        "RIPPLE_RESTORE_REHEARSAL_PASSED": "true",
        "RIPPLE_ACCESSIBILITY_EVIDENCE_PASSED": "true",
        "RIPPLE_BACKUP_ALERT_PATH_TESTED": "true",
        "RIPPLE_RELEASE_RECORD_PREPARED": "true",
    }

    report = module.build_report(ROOT, env)

    assert report["evidence"]["cost_review"]["date_valid"] is False
    assert report["status"] == "blocked"


def test_report_matches_authoritative_launch_gate_variables():
    module = _module()
    launch_gate = (ROOT / "scripts" / "check-aws-launch-readiness.sh").read_text(encoding="utf-8")

    for _, variable in module.EVIDENCE_GATES:
        assert variable in launch_gate
    assert "RIPPLE_COST_REVIEW_DATE" in launch_gate


def test_rendered_report_states_zero_spend_boundary():
    module = _module()
    rendered = module.render_text(module.build_report(ROOT, {}))

    assert "does not contact AWS" in rendered
    assert "authorize spend" in rendered
    assert "check-aws-launch-readiness.sh launch" in rendered
