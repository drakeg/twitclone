# Sprint 19 — Launch Readiness Evidence

**Status:** In implementation.

## Goal

Turn Ripple's existing launch prerequisites into a clear, auditable, zero-spend readiness view so maintainers can see what remains before a future production-launch decision without provisioning infrastructure or weakening any existing gate.

## Story 19.1 — Read-only launch-readiness report

**Status:** In implementation.

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

## Deferred stories

- Evidence-record validation against approved operational records may be considered only if it can be done without committing private operational data.
- AWS provisioning remains separately authorized work and is not part of Sprint 19 by default.
