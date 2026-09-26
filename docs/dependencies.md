# Dependency Management

## Supported runtime

TwitClone currently targets **Python 3.12.x**. The repository-level `.python-version` file is the source of truth for local tooling, CI, the Docker release image, and the initial AWS deployment.

## Dependency files

- `requirements.in` records the direct runtime dependency intent owned by the application.
- `requirements.txt` is the current reproducible runtime install lock, including retained transitive pins and security overrides.
- `requirements-dev.txt` adds development and test tooling on top of the runtime lock.
- `scripts/verify_dependencies.py` verifies the supported Python version and imports the packages used directly by the application.
- `scripts/verify_dependency_lock.py` proves every direct runtime dependency is represented in `requirements.txt` with the same declared version/specifier.
- `scripts/report_dependency_inventory.py` inventories checked-in Python, container-image, GitHub Actions, and Terraform dependency surfaces without network access.

Psycopg 3 with its binary extra is pinned as the production PostgreSQL driver.
SQLite remains part of Python's standard library and needs no package entry.

Install and verify with:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/verify_dependencies.py
python scripts/verify_dependency_lock.py
python scripts/report_dependency_inventory.py
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## Reconciliation decision

Several automated security pull requests were merged on July 23, 2026. Their resulting versions are preserved in `requirements.txt` rather than replaced by a second speculative upgrade.

The file is organized into:

1. Runtime framework dependencies used directly by the Flask application.
2. Explicit application/runtime packages.
3. Transitive packages retained as exact pins after automated security updates.
4. A documented Snyk security override for `zipp`.

This organization does not claim that every transitive pin must remain forever. It records why each class of dependency is present until CI and clean-environment testing provide enough evidence to simplify the lock set safely.

## Upgrade procedure

1. Create a dedicated dependency branch from the latest `main`.
2. For a direct runtime dependency, update `requirements.in` and the matching entry in `requirements.txt` together.
3. Change one coherent dependency group at a time.
4. Install into a clean Python 3.12 virtual environment.
5. Run `python scripts/verify_dependencies.py`.
6. Run `python scripts/verify_dependency_lock.py`.
7. Run the full automated test suite; CI already enforces it on every pull request.
8. Confirm the Docker release image still uses the same Python minor line as `.python-version`.
9. Record vulnerability scan results and any compatibility decisions in the PR.
10. Do not merge multiple overlapping bot PRs without reconciling the final combined result.

## Security bot policy

Dependabot, Mend, Renovate, and Snyk findings are inputs to the engineering process, not automatic proof that a change is safe for this application. Security PRs should be reviewed for:

- overlapping version changes;
- direct versus transitive package intent;
- compatibility with Python 3.12;
- compatibility with Flask and its extensions;
- successful clean installation;
- successful application tests and startup checks.

## Lock-generation boundary

`requirements.in` is currently a direct-dependency **manifest**, not an instruction that `requirements.txt` is generated automatically. The lock remains checked in and deliberately reviewable. A future story may introduce reproducible lock generation only after the exact tool/version, update command, transitive-resolution behavior, and security-bot interaction are documented and tested.


## Runtime version contract

The supported Python **minor** version must stay aligned across:

- `.python-version`
- the Docker base image
- GitHub Actions setup-python configuration
- Renovate's Python update policy
- `scripts/verify_dependencies.py`

Patch releases within Python 3.12 remain allowed. Moving to Python 3.13 or newer requires an explicit compatibility story with CI and release-image validation rather than an isolated bot update.


## Dependency inventory

Run:

```bash
python scripts/report_dependency_inventory.py
python scripts/report_dependency_inventory.py --json
```

The inventory is intentionally local-only. It records the dependency names,
versions/constraints, classifications, and source files currently checked into
the repository. It distinguishes direct, locked, and development Python
dependencies; Dockerfile and production Compose images; GitHub Actions; and
Terraform CLI/provider constraints.

The report does **not** contact package registries, GitHub Marketplace, Docker
registries, or Terraform registries, and it does not claim that a dependency is
current, outdated, vulnerable, or safe. Those judgments still require the
existing security/update tooling plus application compatibility review.

CI runs the inventory command so newly introduced syntax that the repository
cannot classify is surfaced immediately rather than silently omitted.


## Automated update grouping

Renovate remains advisory and **never auto-merges** dependency changes.

Patch updates are grouped by dependency surface so closely related low-risk
changes can be reviewed together.

Renovate's `pip_requirements` manager does not match `.in` files by default, so
`renovate.json` explicitly extends that manager's file patterns to include
`requirements.in`. This is necessary for bot updates to change the direct
manifest and checked-in lock together rather than creating a known CI mismatch.

- direct/runtime Python patch updates across `requirements.in` and
  `requirements.txt`;
- development-only Python patch updates;
- GitHub Actions patch updates;
- Terraform patch updates.

Minor and major updates remain isolated rather than grouped. They require a
focused compatibility review because they are more likely to change behavior or
upgrade contracts.

The Python 3.12 runtime constraints for pyenv and the Docker base image remain
separate guardrails and take precedence over convenience grouping.


## GitHub Actions workflow parsing

CI uses an in-memory SQLite test URL. Keep the `DATABASE_URL` value quoted in
`.github/workflows/ci.yml`, because the unquoted value ending with a colon
caused GitHub Actions to reject the workflow before creating any jobs. The
regression test in `tests/test_ci_workflow_contract.py` guards this detail.
A run that fails with zero jobs must be treated as a workflow-start failure,
not as evidence that the Python, release-image, or Terraform tests ran.
