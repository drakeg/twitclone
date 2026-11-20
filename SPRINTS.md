# Sprint status

The authoritative numbered product roadmap remains `docs/ROADMAP.md`, with
detailed historical sprint records under `docs/sprints/`. This file is the
root-level operational summary required by the Mad Mallard repository standards;
it does not renumber or rewrite completed roadmap history.

## Completed product roadmap

Sprints 0 through 25 are documented as completed in `docs/ROADMAP.md`, subject
to the explicitly documented manual/live launch evidence gates. Do not recreate
completed sprint work.

## Current operating cycle — standards adoption and launch readiness

**Goal:** Keep Ripple continuously shippable, standards-compliant, and ready for
a future explicitly authorized production activation.

Current work:

- [x] Repository-side AWS architecture, validation, backup/restore, plan-policy,
      guarded-apply, budget-alert, and readiness controls implemented.
- [x] Adopt root Mad Mallard governance documents, verified badges, and automated standards checks.
- [x] Clear the current green dependency update queue; continue reviewing new Renovate PRs as they appear.
- [x] Complete the AWS activation handoff documentation.
- [ ] Complete live AWS evidence only after explicit spend authorization.
- [ ] Complete manual accessibility evidence before any public conformance claim.

**Acceptance:** required root governance files exist; README badges are verified
from repository configuration; CI validates the standards contract; existing
tests remain green; no completed roadmap work is restarted.

## Next product/commercial priority

The Issue #372 community operator dashboard pilot and operator-ready demo seed are implemented. Current work standardizes the demo into a one-command, health-checked local launcher before real prospect validation using `docs/PILOT_VALIDATION.md`; further feature expansion should be driven by observed customer pain rather than assumptions. New numbered sprints must be added to `docs/ROADMAP.md` only when real scope is selected, rather than invented solely for process compliance.
