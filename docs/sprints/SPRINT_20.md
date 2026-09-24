# Sprint 20 — Dependency Health and Upgrade Safety

**Status:** In implementation.

## Goal

Make Ripple's dependency and runtime upgrade process explicit, reproducible, and resistant to drift so automated updates cannot silently move one execution environment beyond what CI and release validation actually support.

## Story 20.1 — Python runtime-version contract

**Status:** Completed in PR #262.

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

## Story 20.2 — Direct dependency manifest and lock contract

**Status:** Completed in PR #263.

- Add `requirements.in` as the explicit application-owned direct runtime dependency manifest.
- Keep `requirements.txt` as the checked-in reproducible install lock until a separately reviewed generation workflow exists.
- Add a lightweight standard-library validator that ensures every direct dependency is present in the lock with the same declared version/specifier.
- Run that validator in CI before migrations/tests.
- Fail closed on unsupported requirement syntax rather than silently ignoring an entry.
- Normalize Python distribution names and handle extras such as `psycopg[binary]`.
- Remove stale Issue #13 commentary from the lock and document the current two-file update workflow.

### Acceptance criteria

- The current direct manifest matches the runtime lock.
- A missing direct dependency causes validation to fail.
- Version/specifier drift between the manifest and lock causes validation to fail.
- Normalized names and extras are handled consistently.
- Unsupported requirement syntax is reported explicitly.
- CI runs the lock validator on every pull request.
- Documentation states clearly that the lock is still reviewed/checked in and is not yet automatically generated.

## Story 20.3 — Local dependency-surface inventory

**Status:** In implementation.

- Add a repository-local dependency inventory that uses no network access.
- Distinguish direct, locked, and development Python dependencies.
- Inventory Dockerfile and production Compose images separately from Python packages.
- Inventory GitHub Actions and Terraform CLI/provider constraints.
- Record source file, classification, version/constraint, and parse status for each entry.
- Fail closed when a supported dependency file contains syntax the inventory cannot classify.
- Support both human-readable and JSON output.
- Keep currency/security judgments outside the inventory; it must not claim that a dependency is current, outdated, vulnerable, or safe.

### Acceptance criteria

- The inventory covers Python, container, GitHub Actions, and Terraform surfaces.
- Direct, locked, and development Python dependency intent remains distinguishable.
- The Python release image and production Caddy image are represented.
- CI Actions and Terraform provider/CLI constraints are represented.
- The report explicitly records that it used no network access.
- Unrecognized requirement syntax is surfaced and causes the command to fail.
- CI runs the inventory on every pull request.
- Tests cover all supported surfaces plus local-only/non-currency semantics.

## Planned follow-up stories

- Define coherent grouping/review rules for automated dependency PRs so overlapping bot changes are easier to reconcile.
- Evaluate reproducible lock generation only after tool/version and security-bot behavior are specified.

## Boundary

Sprint 20 changes dependency/runtime maintenance only. It does not authorize AWS provisioning, new paid services, dependency auto-merge, or skipping application compatibility tests.
