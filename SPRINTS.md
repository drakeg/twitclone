# Sprint status

The authoritative numbered product roadmap remains `docs/ROADMAP.md`, with
detailed historical sprint records under `docs/sprints/`. This file is the
root-level operational summary required by the Mad Mallard repository standards;
it does not renumber or rewrite completed roadmap history.

## Completed product roadmap

Sprints 0 through 35 are documented as completed in `docs/ROADMAP.md`, subject
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

## Completed product sprint — Sprint 33

**Goal:** Add durable Space announcements and operator communication.

Completed work:

- [x] Story 33.1 — Persistent member-only operator announcements.
- [x] Story 33.2 — Non-destructive announcement lifecycle and audit.
- [x] Story 33.3 — Per-member read state and sprint regression hardening.

See `docs/sprints/SPRINT_33.md` for acceptance criteria and scope boundaries.

## Completed product sprint — Sprint 34

**Goal:** Add timezone-safe Space events and meetups.

Completed work:

- [x] Story 34.1 — Timezone-safe upcoming events.
- [x] Story 34.2 — Non-destructive event lifecycle and audit.
- [x] Story 34.3 — Aggregate-only member RSVP state and sprint regression hardening.

See `docs/sprints/SPRINT_34.md` for acceptance criteria and scope boundaries.

## Completed product sprint — Sprint 35

**Goal:** Add private Space calendar portability.

Completed work:

- [x] Story 35.1 — Member-only iCalendar export.
- [x] Story 35.2 — Individual event calendar download.
- [x] Story 35.3 — Calendar regression hardening.

See `docs/sprints/SPRINT_35.md` for acceptance criteria and scope boundaries.

## Active product sprint — Sprint 36

**Goal:** Add a privacy-first Space member directory.

Current work:

- [x] Story 36.1 — Opt-in member directory.
- [ ] Story 36.2 — Directory role filtering/profile-card usability (implementation in review).
- [ ] Story 36.3 — Directory regression hardening.

See `docs/sprints/SPRINT_36.md` for acceptance criteria and scope boundaries.

## Next product/commercial priority

Commercialization validation for Issue #372 continues in parallel with product development; it is not a stop condition for the roadmap. Product work may follow an "if you build it, they will come" path when it meaningfully improves Ripple. Customer evidence can reprioritize work, but lack of customer evidence does not halt an active Sprint or backlog. Sprint 36 continues improving Ripple's Space/community product while preserving the existing launch, safety, cost, and standards gates. New numbered sprints must be added to `docs/ROADMAP.md` only when real scope is selected, rather than invented solely for process compliance.
