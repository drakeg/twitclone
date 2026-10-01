"""Validate a sanitized manual accessibility evidence record offline."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


FORMAT = "ripple-accessibility-evidence"
VERSION = 1
RELEASE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_SCENARIOS = {
    "nvda-sign-in": ("NVDA", "Windows", 100),
    "nvda-timeline": ("NVDA", "Windows", 100),
    "nvda-create-post": ("NVDA", "Windows", 100),
    "nvda-follow": ("NVDA", "Windows", 100),
    "nvda-notifications": ("NVDA", "Windows", 100),
    "nvda-messaging": ("NVDA", "Windows", 100),
    "voiceover-timeline": ("VoiceOver", "macOS", 100),
    "voiceover-profile-editing": ("VoiceOver", "macOS", 100),
    "voiceover-messaging": ("VoiceOver", "macOS", 100),
    "voiceover-moderation": ("VoiceOver", "macOS", 100),
    "zoom-200-core-flows": ("none", None, 200),
    "zoom-400-core-flows": ("none", None, 400),
}
ALLOWED_RESULTS = {"pass", "fail", "blocked"}
ALLOWED_RETEST_RESULTS = {None, "pass", "fail", "blocked", "not_required"}
ALLOWED_DECISIONS = {"approved", "blocked"}
PLACEHOLDER_PREFIX = "replace-with-"


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _is_placeholder(value):
    return isinstance(value, str) and value.startswith(PLACEHOLDER_PREFIX)


def validate_record(record):
    errors = []
    if not isinstance(record, dict):
        return ["record must be a JSON object"]
    if record.get("format") != FORMAT:
        errors.append(f"format must be {FORMAT!r}")
    if record.get("version") != VERSION:
        errors.append(f"version must be {VERSION}")

    release_sha = record.get("release_sha")
    if not isinstance(release_sha, str) or not RELEASE_SHA_RE.fullmatch(release_sha):
        errors.append("release_sha must be an exact 40-character lowercase Git SHA")

    review_date = record.get("review_date")
    try:
        date.fromisoformat(review_date)
    except (TypeError, ValueError):
        errors.append("review_date must be YYYY-MM-DD")

    if not _nonempty_string(record.get("operator")):
        errors.append("operator must be a non-empty string or opaque operator reference")

    decision = record.get("review_decision")
    if decision not in ALLOWED_DECISIONS:
        errors.append("review_decision must be approved or blocked")

    scenarios = record.get("scenarios")
    if not isinstance(scenarios, list):
        errors.append("scenarios must be an array")
        return errors

    by_id = {}
    for index, scenario in enumerate(scenarios):
        prefix = f"scenarios[{index}]"
        if not isinstance(scenario, dict):
            errors.append(f"{prefix} must be an object")
            continue
        scenario_id = scenario.get("scenario_id")
        if not _nonempty_string(scenario_id):
            errors.append(f"{prefix}.scenario_id must be non-empty")
            continue
        if scenario_id in by_id:
            errors.append(f"duplicate scenario_id: {scenario_id}")
            continue
        by_id[scenario_id] = scenario

        result = scenario.get("result")
        if result not in ALLOWED_RESULTS:
            errors.append(f"{scenario_id}.result must be pass, fail, or blocked")

        retest = scenario.get("retest_result")
        if retest not in ALLOWED_RETEST_RESULTS:
            errors.append(f"{scenario_id}.retest_result is invalid")

        for field in ("browser", "browser_version", "viewport"):
            value = scenario.get(field)
            if not _nonempty_string(value):
                errors.append(f"{scenario_id}.{field} must be non-empty")

        if result in {"fail", "blocked"} and not _nonempty_string(scenario.get("defect_reference")):
            errors.append(f"{scenario_id}.defect_reference is required when result is {result}")

    missing = sorted(set(REQUIRED_SCENARIOS) - set(by_id))
    if missing:
        errors.append("missing required scenarios: " + ", ".join(missing))

    for scenario_id, (expected_at, expected_platform, expected_zoom) in REQUIRED_SCENARIOS.items():
        scenario = by_id.get(scenario_id)
        if scenario is None:
            continue
        if scenario.get("assistive_technology") != expected_at:
            errors.append(f"{scenario_id}.assistive_technology must be {expected_at}")
        if expected_platform is not None and scenario.get("platform") != expected_platform:
            errors.append(f"{scenario_id}.platform must be {expected_platform}")
        if scenario.get("zoom_percent") != expected_zoom:
            errors.append(f"{scenario_id}.zoom_percent must be {expected_zoom}")
        if expected_at == "NVDA" and scenario.get("browser") not in {"Firefox", "Chrome"}:
            errors.append(f"{scenario_id}.browser must be Firefox or Chrome")
        if expected_at == "VoiceOver" and scenario.get("browser") != "Safari":
            errors.append(f"{scenario_id}.browser must be Safari")

    if decision == "approved":
        for scenario_id in REQUIRED_SCENARIOS:
            scenario = by_id.get(scenario_id)
            if scenario is None:
                continue
            effective = scenario.get("retest_result") if scenario.get("retest_result") not in {None, "not_required"} else scenario.get("result")
            if effective != "pass":
                errors.append(f"{scenario_id} must have an effective pass result before approval")
            for field in ("browser", "browser_version", "viewport", "platform"):
                value = scenario.get(field)
                if _is_placeholder(value):
                    errors.append(f"{scenario_id}.{field} still contains a template placeholder")
            if scenario.get("assistive_technology") != "none":
                value = scenario.get("assistive_technology_version")
                if not _nonempty_string(value) or _is_placeholder(value):
                    errors.append(f"{scenario_id}.assistive_technology_version must record the tested version")

    return errors


def validate_path(path):
    try:
        record = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"unable to read valid JSON: {exc}"]
    return record, validate_record(record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", help="path to a local accessibility evidence JSON record")
    parser.add_argument("--json", action="store_true", help="emit machine-readable validation output")
    args = parser.parse_args()

    record, errors = validate_path(args.record)
    decision = record.get("review_decision") if isinstance(record, dict) else None
    payload = {
        "format": FORMAT,
        "version": VERSION,
        "record_valid": not errors,
        "review_decision": decision,
        "launch_gate_satisfied": False,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif errors:
        print("Accessibility evidence record is invalid:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Accessibility evidence record is structurally valid.")
        print(f"Review decision: {decision}")
        print("This validator does not satisfy or set the launch gate.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
