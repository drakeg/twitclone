#!/usr/bin/env python3
"""Report Ripple launch-readiness evidence without provisioning infrastructure."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import date, datetime, timezone
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


def load_evidence_metadata(path: Path | None) -> dict:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evidence metadata must be a JSON object")
    return payload


def _record_freshness(record: dict, as_of: date) -> dict:
    record_date = record.get("date")
    review_after_days = record.get("review_after_days")
    if not record_date or review_after_days is None:
        return {"status": "not_evaluated", "age_days": None, "review_after_days": review_after_days}
    if not isinstance(review_after_days, int) or review_after_days < 0:
        return {"status": "invalid", "age_days": None, "review_after_days": review_after_days}
    try:
        recorded = date.fromisoformat(record_date)
    except (TypeError, ValueError):
        return {"status": "invalid", "age_days": None, "review_after_days": review_after_days}
    age_days = (as_of - recorded).days
    if age_days < 0:
        return {"status": "invalid", "age_days": age_days, "review_after_days": review_after_days}
    return {
        "status": "stale" if age_days > review_after_days else "fresh",
        "age_days": age_days,
        "review_after_days": review_after_days,
    }


def build_report(
    root: Path = ROOT,
    environ: dict[str, str] | None = None,
    metadata: dict | None = None,
    as_of: date | None = None,
) -> dict:
    env = os.environ if environ is None else environ
    metadata = {} if metadata is None else metadata
    as_of = date.today() if as_of is None else as_of
    artifacts = {path: {"present": (root / path).is_file()} for path in REQUIRED_ARTIFACTS}

    evidence = {}
    for name, variable in EVIDENCE_GATES:
        record = metadata.get(name, {})
        if not isinstance(record, dict):
            record = {}
        freshness = _record_freshness(record, as_of)
        evidence[name] = {
            "complete": _is_true(env.get(variable)),
            "source": variable,
            "record_present": bool(record),
            "record_date": record.get("date"),
            "record_reference": record.get("reference"),
            "freshness": freshness,
        }

    cost_date = env.get("RIPPLE_COST_REVIEW_DATE")
    evidence["cost_review"]["date"] = cost_date
    evidence["cost_review"]["date_valid"] = bool(cost_date and _DATE_RE.fullmatch(cost_date))

    missing_artifacts = sorted(path for path, item in artifacts.items() if not item["present"])
    incomplete_evidence = sorted(
        name
        for name, item in evidence.items()
        if not item["complete"] or (name == "cost_review" and not item["date_valid"])
    )

    evidence_records = {
        name: {
            "present": item["record_present"],
            "date": item["record_date"],
            "reference": item["record_reference"],
            "freshness": item["freshness"],
        }
        for name, item in evidence.items()
    }
    freshness_attention = sorted(
        name
        for name, item in evidence_records.items()
        if item["freshness"]["status"] in {"stale", "invalid"}
    )

    return {
        "status": "ready_for_launch_gate_review" if not missing_artifacts and not incomplete_evidence else "blocked",
        "authoritative_gate": "scripts/check-aws-launch-readiness.sh launch",
        "spend_authorized": False,
        "provisioning_performed": False,
        "artifacts": artifacts,
        "evidence": evidence,
        "evidence_records": evidence_records,
        "freshness_attention": freshness_attention,
        "as_of_date": as_of.isoformat(),
        "missing_artifacts": missing_artifacts,
        "incomplete_evidence": incomplete_evidence,
    }


def _snapshot_checksum(payload: dict) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def build_snapshot(
    report: dict,
    release_sha: str | None = None,
    captured_at: datetime | None = None,
) -> dict:
    captured_at = datetime.now(timezone.utc) if captured_at is None else captured_at
    if captured_at.tzinfo is None:
        raise ValueError("captured_at must be timezone-aware")
    if release_sha is not None and not re.fullmatch(r"[0-9a-f]{40}", release_sha):
        raise ValueError("release_sha must be a 40-character lowercase Git SHA")
    snapshot = {
        "format": "ripple-launch-readiness-snapshot",
        "version": 1,
        "captured_at": captured_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "release_sha": release_sha,
        "status": report["status"],
        "authoritative_gate": report["authoritative_gate"],
        "spend_authorized": False,
        "provisioning_performed": False,
        "as_of_date": report["as_of_date"],
        "missing_artifacts": report["missing_artifacts"],
        "incomplete_evidence": report["incomplete_evidence"],
        "freshness_attention": report["freshness_attention"],
        "evidence_records": report["evidence_records"],
    }
    snapshot["checksum"] = {
        "algorithm": "sha256",
        "value": _snapshot_checksum(snapshot),
    }
    return snapshot


def verify_snapshot_checksum(snapshot: dict) -> bool:
    checksum = snapshot.get("checksum")
    if not isinstance(checksum, dict):
        return False
    if checksum.get("algorithm") != "sha256":
        return False
    expected = checksum.get("value")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        return False
    payload = dict(snapshot)
    payload.pop("checksum", None)
    return _snapshot_checksum(payload) == expected


def render_text(report: dict) -> str:
    lines = [f"Launch readiness status: {report['status']}", "", "Evidence gates:"]
    for name, item in report["evidence"].items():
        complete = item["complete"]
        if name == "cost_review":
            complete = complete and item["date_valid"]
        lines.append(f"- {name}: {'complete' if complete else 'missing'}")

    lines.extend(["", "Evidence records:"])
    for name, item in report["evidence_records"].items():
        if item["present"]:
            suffix = f" ({item['date']})" if item["date"] else ""
            freshness = item["freshness"]["status"]
            detail = ""
            if freshness in {"fresh", "stale"}:
                detail = (
                    f"; freshness={freshness}, age={item['freshness']['age_days']}d, "
                    f"review_after={item['freshness']['review_after_days']}d"
                )
            elif freshness == "invalid":
                detail = "; freshness=invalid"
            lines.append(f"- {name}: metadata present{suffix}{detail}")
        else:
            lines.append(f"- {name}: no metadata supplied")

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
    parser.add_argument(
        "--evidence-metadata",
        type=Path,
        help="optional path to sanitized evidence-record metadata JSON",
    )
    parser.add_argument(
        "--as-of-date",
        type=date.fromisoformat,
        help="optional YYYY-MM-DD date for deterministic freshness review",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="write a sanitized JSON readiness snapshot to this local path",
    )
    parser.add_argument(
        "--release-sha",
        help="optional exact 40-character lowercase Git SHA to record in the snapshot",
    )
    parser.add_argument(
        "--verify-snapshot",
        type=Path,
        help="verify a previously written readiness snapshot checksum and exit",
    )
    args = parser.parse_args()
    if args.verify_snapshot:
        payload = json.loads(args.verify_snapshot.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not verify_snapshot_checksum(payload):
            print("INVALID: readiness snapshot checksum does not match", file=os.sys.stderr)
            return 1
        print("OK: readiness snapshot checksum verified")
        return 0

    metadata = load_evidence_metadata(args.evidence_metadata)
    report = build_report(metadata=metadata, as_of=args.as_of_date)
    if args.snapshot:
        snapshot = build_snapshot(report, release_sha=args.release_sha)
        args.snapshot.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
