# Sprint 19 — Launch Readiness Evidence

**Status:** In implementation.

## Goal

Turn Ripple's existing launch prerequisites into a clear, auditable, zero-spend readiness view so maintainers can see what remains before a future production-launch decision without provisioning infrastructure or weakening any existing gate.

## Story 19.1 — Read-only launch-readiness report

**Status:** Completed in PR #255.

- Add a read-only report that summarizes required repository artifacts and the same manual evidence acknowledged by the authoritative launch gate.
- Report missing accessibility evidence, restore rehearsal, backup-alert-path test, cost review/date, and release-record preparation individually.
- Support both human-readable and JSON output for local/operator use.
- Keep `scripts/check-aws-launch-readiness.sh launch` authoritative for the actual launch gate.
- Never contact AWS, invoke Terraform, provision infrastructure, or treat the report as spend authorization.
- Preserve the existing no-spend boundary and deferred AWS activation.

### Acceptance criteria

- Running the report with no evidence acknowledgments returns a blocked status and names incomplete gates.
- Complete evidence acknowledgments plus required repository artifacts return `ready_for_launch_gate_review`.
- An invalid or missing cost-review date keeps the report blocked.
- The report consumes the same evidence environment-variable names as the existing launch gate.
- The report explicitly states that it is read-only, does not contact AWS, does not authorize spend, and does not replace the launch gate.
- Tests cover blocked, ready, malformed-date, variable-alignment, and zero-spend messaging behavior.

## Story 19.2 — Sanitized evidence-record metadata

**Status:** Completed in PR #256.

- Allow the readiness report to consume an optional local JSON file containing only sanitized evidence-record dates and opaque references.
- Keep evidence metadata advisory: a supplied record reference must never turn an incomplete gate into a completed one.
- Keep completed operational records, credentials, infrastructure identifiers, and private environment details outside the repository.
- Show supplied record metadata in both text and JSON output so operators can connect readiness acknowledgments to their approved record system.
- Validate that the metadata file is a JSON object and fail clearly on malformed structure.
- Provide a repository-safe example containing placeholders only.

### Acceptance criteria

- A supplied metadata record is visible in the report without changing the gate's completion status.
- Missing metadata remains distinguishable from missing evidence acknowledgement.
- Non-object metadata is rejected.
- Text output shows the sanitized record date when supplied.
- Tests prove metadata cannot authorize a launch gate.
- Documentation explains that completed operational records remain outside the repository.

## Story 19.3 — Advisory evidence freshness review

**Status:** Completed in PR #257.

- Let sanitized evidence metadata optionally declare a `review_after_days` window per record.
- Compare dated evidence against an explicit report `--as-of-date` or the local current date.
- Classify records as fresh, stale, invalid, or not evaluated.
- Keep freshness advisory: stale metadata must be surfaced for human review but must not silently pass or fail the authoritative launch gate.
- Define no repository-wide default freshness periods; review windows remain explicit operational policy supplied with the sanitized metadata.
- Treat future-dated records, invalid dates, and invalid review windows as review-attention items.

### Acceptance criteria

- A record with an explicit review window becomes stale only when its age exceeds that window.
- Records without a review window remain `not_evaluated` rather than receiving an invented policy.
- Stale or invalid record metadata appears in a `freshness_attention` list.
- Freshness status does not override the existing evidence acknowledgments or authoritative launch gate.
- `--as-of-date` supports deterministic review/testing.
- Human-readable output includes age and review-window details for fresh/stale records.
- Tests cover stale, not-evaluated, invalid, advisory-only, and rendered-output behavior.

## Story 19.4 — Sanitized readiness snapshot

**Status:** In implementation.

- Allow maintainers to write a versioned local JSON snapshot of the current readiness report for attachment to an approved release record.
- Include status, review date, incomplete gates, missing repository artifacts, freshness-attention items, sanitized evidence-record metadata, and an optional immutable release SHA.
- Exclude environment-variable names/values, secrets, full operational records, infrastructure identifiers, and provisioning details from the snapshot.
- Require any supplied release SHA to be an exact 40-character lowercase Git SHA.
- Record a timezone-aware UTC capture timestamp.
- Keep snapshot generation read-only and local; writing a snapshot must not change launch readiness, provision infrastructure, or authorize spend.

### Acceptance criteria

- Snapshot output has an explicit format name and version.
- A deterministic capture time and release SHA can be represented in tests.
- Invalid/non-immutable release SHA values are rejected.
- Naive capture timestamps are rejected.
- Snapshot serialization excludes evidence environment-variable names and unrelated secret values.
- Snapshot generation preserves `spend_authorized: false` and `provisioning_performed: false`.
- Tests cover shape, identity validation, timestamp validation, and sensitive-input exclusion.

## Deferred stories

- Stronger validation against approved operational records may be considered only if it can be done without copying private operational data into source control or contacting a new paid service.
- AWS provisioning remains separately authorized work and is not part of Sprint 19 by default.
