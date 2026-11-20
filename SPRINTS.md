# Sprint status

The authoritative numbered product roadmap remains `docs/ROADMAP.md`, with
detailed historical sprint records under `docs/sprints/`. This file is the
root-level operational summary required by the Mad Mallard repository standards;
it does not renumber or rewrite completed roadmap history.

## Completed product roadmap

Sprints 0 through 25 are documented as completed in `docs/ROADMAP.md`, subject
to the explicitly documented manual/live launch evidence gates. Do not recreate
completed sprint work.

## Current operating cycle — launch readiness and commercialization validation

**Goal:** Keep Ripple continuously shippable and standards-compliant while
moving the SMB member-community pilot from verified demo readiness to real
prospect evidence, without bypassing production launch gates.

Current work:

- [x] Repository-side AWS architecture, validation, backup/restore, plan-policy,
      guarded-apply, budget-alert, and readiness controls implemented.
- [x] Adopt root Mad Mallard governance documents, verified badges, and automated standards checks.
- [x] Clear the current green dependency update queue; continue reviewing new Renovate PRs as they appear.
- [x] Complete the AWS activation handoff documentation.
- [ ] Complete live AWS evidence only after explicit spend authorization.
- [ ] Complete manual accessibility evidence before any public conformance claim.
- [x] Verify the SMB operator pilot in the local/LAN Docker environment, including migration, health, idempotent seeding, authenticated owner workflow, and lean runtime images.

**Acceptance:** required root governance files exist; README badges are verified
from repository configuration; CI validates the standards contract; existing
tests remain green; no completed roadmap work is restarted.

## Active product sprint — Sprint 26

**Goal:** Add safe Space ownership handoff and member-administration workflows.

Current work:

- [x] Story 26.1 — Safe ownership transfer.
- [ ] Story 26.2 — Owner member removal (in progress).
- [ ] Story 26.3 — Membership administration audit.

See `docs/sprints/SPRINT_26.md` for acceptance criteria and scope boundaries.

## Next product/commercial priority

Commercialization validation for Issue #372 continues in parallel with product development; it is not a stop condition for the roadmap. Sprint 26 continues improving Ripple's Space/community product while preserving the existing launch, safety, cost, and standards gates. New numbered sprints must be added to `docs/ROADMAP.md` only when real scope is selected, rather than invented solely for process compliance.
