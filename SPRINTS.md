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

## Next product/commercial priority

The Issue #372 community operator dashboard pilot has completed engineering/demo readiness. The local/LAN Docker workflow, migration, readiness check, idempotent demo seed, CSRF-protected owner login, operator dashboard, and lean runtime image boundary have all been verified. The next product gate is real prospect validation using `docs/PILOT_VALIDATION.md`; further feature expansion should be driven by repeated customer pain rather than assumptions. New numbered sprints must be added to `docs/ROADMAP.md` only when real scope is selected, rather than invented solely for process compliance.
