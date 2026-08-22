# ADR-0040: Standard release and recovery evidence records

- Status: Accepted
- Date: 2026-08-21
- Sprint: 6
- Story: 6.8

## Context

Ripple's runbooks define launch gates, recovery objectives, preflight checks,
and restore procedures. Free-form operator notes can still omit the exact image,
backup, timing, alert, or approval evidence needed to decide whether a release
is safe and whether a rehearsal met its objectives.

## Decision

- Maintain reusable release-readiness and restore-rehearsal record templates
  alongside the runbooks.
- Require an owner, UTC timing, evidence location, result, and disposition for
  each launch or recovery gate.
- Record the immutable release SHA and image digest, prior known-good artifact,
  migration decision, recovery-set identifiers, preflight and smoke-test
  results, monitoring ownership, and final approval or block decision.
- Keep completed operational records in the approved operations system rather
  than the public source repository.
- Never place credentials, secret values, database URLs, customer data, or
  private infrastructure details in the templates or completed public files.

## Consequences

- Operators can execute and review releases and rehearsals against one stable
  evidence contract.
- Repository tests prevent important launch-gate fields from disappearing from
  the templates accidentally.
- The templates do not perform or approve a deployment; the named operator and
  reviewer remain responsible for validating the evidence.
- Local application behavior, dependencies, and UI are unchanged. The Compose
  test service mounts the current checkout read-only so its documented command
  cannot silently execute stale tests from a cached image.
