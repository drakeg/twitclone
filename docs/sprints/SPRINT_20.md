# Sprint 20 — Dependency Health and Upgrade Safety

**Status:** Completed.

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

**Status:** Completed in PR #264.

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

## Story 20.4 — Conservative automated-update grouping

**Status:** Completed in PR #265.

- Keep Renovate auto-merge disabled globally and in all explicit grouping rules.
- Group patch updates by dependency surface so low-risk changes can be reviewed coherently.
- Group runtime Python patch updates across `requirements.in` and `requirements.txt` so the direct manifest and lock move together.
- Keep development-only Python, GitHub Actions, and Terraform patch updates in separate review groups.
- Leave minor and major updates ungrouped for focused compatibility review.
- Preserve the existing Python 3.12 pyenv/Docker constraints.
- Add regression coverage for grouping, no-auto-merge, and runtime guardrails.

### Acceptance criteria

- Renovate cannot auto-merge any dependency update under the repository config.
- Runtime Python patch changes are grouped across the direct manifest and runtime lock.
- Development Python, GitHub Actions, and Terraform patch changes use separate surface-specific groups.
- Minor and major updates remain isolated.
- Python 3.12 runtime constraints remain present.
- Tests fail if auto-merge is enabled or grouping/guardrails drift.
- Documentation describes the review policy and why minor/major changes stay separate.

## Lock-generation decision

Automatic lock generation is deferred.

The repository now has an explicit direct-dependency manifest, a checked-in runtime lock, CI verification that the two remain aligned, a local dependency inventory, and conservative automated-update grouping. There is no pinned lock compiler, documented resolver behavior, or established Renovate/Mend/Snyk workflow for a generated lock. Adding a compiler now would create a new maintenance dependency without yet improving the review contract.

A future lock-generation story must first define:

- the exact tool and pinned tool version;
- the exact generation command and Python runtime;
- deterministic resolver/upgrade behavior;
- how direct-dependency changes and transitive changes are represented in review;
- how Renovate, Mend, Snyk, and other security automation interact with the generated file;
- CI proof that a regenerated lock is reproducible and does not introduce unreviewed drift.

Until then, `requirements.in` remains the direct-dependency intent manifest and `requirements.txt` remains the checked-in reproducible install lock.


## Boundary

Sprint 20 changes dependency/runtime maintenance only. It does not authorize AWS provisioning, new paid services, dependency auto-merge, or skipping application compatibility tests.


## Sprint outcome

Sprint 20 established a coherent dependency-maintenance contract without enabling unattended upgrades. Python runtime alignment is enforced across local tooling, CI, Docker, Renovate, and dependency verification. Direct runtime intent is separated from the install lock and checked in CI. Dependency surfaces can be inventoried locally without network access, and Renovate patch updates are grouped conservatively while minor/major updates stay isolated.

## Definition of done

Completed. Dependency/runtime drift now has explicit repository contracts and regression coverage, while automatic lock generation remains intentionally deferred until its tooling and security-automation semantics can be specified and tested.
