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

**Status:** In implementation.

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

## Deferred stories

- Stronger validation against approved operational records may be considered only if it can be done without copying private operational data into source control or contacting a new paid service.
- AWS provisioning remains separately authorized work and is not part of Sprint 19 by default.
