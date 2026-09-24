# Sprint 20 — Dependency Health and Upgrade Safety

**Status:** In implementation.

## Goal

Make Ripple's dependency and runtime upgrade process explicit, reproducible, and resistant to drift so automated updates cannot silently move one execution environment beyond what CI and release validation actually support.

## Story 20.1 — Python runtime-version contract

**Status:** In implementation.

- Treat `.python-version` as the source of truth for the supported Python minor line.
- Align the Docker release image with the same Python 3.12 minor line used by CI.
- Require `scripts/verify_dependencies.py` to reject unsupported Python minor versions rather than accepting any newer interpreter.
- Constrain Renovate so pyenv and Dockerfile Python updates remain on the supported 3.12 line.
- Add regression coverage that keeps `.python-version`, Docker, CI, Renovate, and the dependency verifier aligned.
- Update dependency documentation to reflect that the full automated test suite is already active in CI.

### Acceptance criteria

- The Docker release image uses Python 3.12 rather than a newer untested minor line.
- CI and the Docker image resolve to the same supported Python minor version.
- The dependency verifier rejects Python 3.13+ until an explicit compatibility story changes the contract.
- Renovate cannot automatically advance either pyenv or Docker Python beyond 3.12.
- Tests fail if runtime-version sources drift apart.
- Dependency documentation no longer refers to already-completed Issue #13 as future work.

## Planned follow-up stories

- Evaluate a smaller direct-dependency input plus a reproducibly generated lock file.
- Add dependency-drift reporting that distinguishes direct, transitive, runtime, CI action, Docker image, and Terraform provider updates.
- Define coherent grouping/review rules for automated dependency PRs so overlapping bot changes are easier to reconcile.

## Boundary

Sprint 20 changes dependency/runtime maintenance only. It does not authorize AWS provisioning, new paid services, dependency auto-merge, or skipping application compatibility tests.
