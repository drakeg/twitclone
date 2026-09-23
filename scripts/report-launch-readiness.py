#!/usr/bin/env python3
"""Report Ripple launch-readiness evidence without provisioning infrastructure."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ARTIFACTS = (
    "compose.production.yaml",
    "deploy/bootstrap-host.sh",
    "deploy/Caddyfile",
    "deploy/env.production.example",
    "scripts/build-release-image.sh",
    "scripts/render-production-env.sh",
    "scripts/deploy-production.sh",
    "scripts/dry-run-production-release.sh",
    "scripts/check-aws-launch-readiness.sh",
    "infra/terraform/main.tf",
    "infra/terraform/variables.tf",
    "infra/terraform/outputs.tf",
    "docs/operations.md",
    "docs/templates/release-readiness-record.md",
    "docs/templates/restore-rehearsal-record.md",
)

EVIDENCE_GATES = (
    ("cost_review", "RIPPLE_COST_REVIEWED"),
    ("restore_rehearsal", "RIPPLE_RESTORE_REHEARSAL_PASSED"),
    ("accessibility_evidence", "RIPPLE_ACCESSIBILITY_EVIDENCE_PASSED"),
    ("backup_alert_path", "RIPPLE_BACKUP_ALERT_PATH_TESTED"),
    ("release_record", "RIPPLE_RELEASE_RECORD_PREPARED"),
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _is_true(value: str | None) -> bool:
    return value == "true"


def build_report(root: Path = ROOT, environ: dict[str, str] | None = None) -> dict:
    env = os.environ if environ is None else environ
    artifacts = {path: {"present": (root / path).is_file()} for path in REQUIRED_ARTIFACTS}

    evidence = {}
    for name, variable in EVIDENCE_GATES:
        evidence[name] = {"complete": _is_true(env.get(variable)), "source": variable}

    cost_date = env.get("RIPPLE_COST_REVIEW_DATE")
    evidence["cost_review"]["date"] = cost_date
    evidence["cost_review"]["date_valid"] = bool(cost_date and _DATE_RE.fullmatch(cost_date))

    missing_artifacts = sorted(path for path, item in artifacts.items() if not item["present"])
    incomplete_evidence = sorted(
        name
        for name, item in evidence.items()
        if not item["complete"] or (name == "cost_review" and not item["date_valid"])
    )

    return {
        "status": "ready_for_launch_gate_review" if not missing_artifacts and not incomplete_evidence else "blocked",
        "authoritative_gate": "scripts/check-aws-launch-readiness.sh launch",
        "spend_authorized": False,
        "provisioning_performed": False,
        "artifacts": artifacts,
        "evidence": evidence,
        "missing_artifacts": missing_artifacts,
        "incomplete_evidence": incomplete_evidence,
    }


def render_text(report: dict) -> str:
    lines = [f"Launch readiness status: {report['status']}", "", "Evidence gates:"]
    for name, item in report["evidence"].items():
        complete = item["complete"]
        if name == "cost_review":
            complete = complete and item["date_valid"]
        lines.append(f"- {name}: {'complete' if complete else 'missing'}")

    lines.extend(["", "Repository artifacts:"])
    if report["missing_artifacts"]:
        for path in report["missing_artifacts"]:
            lines.append(f"- missing: {path}")
    else:
        lines.append("- all required artifacts present")

    lines.extend([
        "",
        "This report is read-only. It does not contact AWS, provision resources,",
        "authorize spend, or replace the authoritative launch gate:",
        f"  {report['authoritative_gate']}",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
